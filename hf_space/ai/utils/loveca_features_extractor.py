import gymnasium as gym
import torch
import torch.nn as nn
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor


class CardEncoder(nn.Module):
    """
    Shared encoder for single cards.
    Input: [Batch, ..., 64] -> Output: [Batch, ..., EmbedDim]
    Optimized: Reduced layer count, removed intermediate LayerNorm.
    """

    def __init__(self, input_dim=64, embed_dim=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, embed_dim),
            nn.LayerNorm(embed_dim),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)


class MultiHeadCardAttention(nn.Module):
    """
    Self-Attention block for handling sets of cards.
    Optimized: Removed post-norm in favor of pre-norm style if desired,
    but keeping it simple: just standard MHA is fine.
    """

    def __init__(self, embed_dim=128, num_heads=4):
        super().__init__()
        # batch_first=True is critical for speed with our data layout
        self.attn = nn.MultiheadAttention(embed_dim, num_heads, batch_first=True)
        self.norm = nn.LayerNorm(embed_dim)

    def forward(self, x, mask=None):
        # Flattened logic for speed:
        # Pre-Norm (Original was Post-Norm, let's keep Post-Norm but optimized)

        # Robustness handling:
        if mask is not None:
            # Fast check: are any masked?
            if mask.any():
                all_masked = mask.all(dim=1, keepdim=True)
                mask = mask & (~all_masked)

        # MHA
        attn_out, _ = self.attn(x, x, x, key_padding_mask=mask, need_weights=False)

        # Add & Norm
        return self.norm(x + attn_out)


class LovecaFeaturesExtractor(BaseFeaturesExtractor):
    """
    Custom Feature Extractor for Love Live TCG.
    Parses the 2240-dim structured observation into semantic components.
    """

    def __init__(self, observation_space: gym.spaces.Box, features_dim: int = 256):
        super().__init__(observation_space, features_dim)

        self.card_dim = 64
        self.embed_dim = 128  # Consider reducing to 64 if speed is critical? No, keep 128 for quality.

        # Calculate offsets based on 2240 layout
        # Hand (15) + HandOver (1) + Stage (3) + Live (3) + LiveSucc (3) + OppStage (3) + OppHist (6) = 34 Cards
        # 34 * 64 = 2176
        # Global = 64
        # Total = 2240

        self.n_hand = 16  # 15 + 1
        self.n_stage = 3
        self.n_live = 6  # 3 Pending + 3 Success
        self.n_opp = 9  # 3 Stage + 6 History

        # 1. Shared Card Encoder
        self.card_encoder = CardEncoder(self.card_dim, self.embed_dim)

        # 2. Attention Blocks
        self.hand_attention = MultiHeadCardAttention(self.embed_dim, num_heads=4)
        self.opp_attention = MultiHeadCardAttention(self.embed_dim, num_heads=2)

        # 3. Embeddings/Projections
        # Positional Embeddings for fixed slot zones (Stage, Live, OppStage)
        self.stage_pos_emb = nn.Parameter(torch.randn(1, 3, self.embed_dim))
        self.live_pos_emb = nn.Parameter(torch.randn(1, 6, self.embed_dim))
        self.opp_pos_emb = nn.Parameter(torch.randn(1, 9, self.embed_dim))

        # 4. Fusion
        # Inputs to fusion:
        # - Hand (16 * 128): 2048
        # - Stage (3 * 128): 384
        # - Live (6 * 128): 768
        # - Opp Summary (Mean Pool): 128
        # - Global: 64
        # Total Fusion Input: 2048+384+768+128+64 = 3392

        self.fusion_dim = 3392
        self.fusion_net = nn.Sequential(
            nn.Linear(self.fusion_dim, 512),
            nn.ReLU(inplace=True),
            nn.Linear(512, features_dim),
            nn.LayerNorm(features_dim),
            nn.ReLU(inplace=True),
        )

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        batch_size = observations.shape[0]

        # 1. Slice Observation
        hand_flat = observations[:, :1024]
        stage_flat = observations[:, 1024:1216]
        live_flat = observations[:, 1216:1600]
        opp_flat = observations[:, 1600:2176]
        global_features = observations[:, 2176:]

        # 2. Reshape & Encode
        hand_cards = hand_flat.reshape(batch_size, 16, 64)
        stage_cards = stage_flat.reshape(batch_size, 3, 64)
        live_cards = live_flat.reshape(batch_size, 6, 64)
        opp_cards = opp_flat.reshape(batch_size, 9, 64)

        # Create Masks (Presence bit is index 0)
        hand_mask = hand_cards[:, :, 0] < 0.5
        opp_mask = opp_cards[:, :, 0] < 0.5

        # Encode All Cards
        hand_emb = self.card_encoder(hand_cards)
        stage_emb = self.card_encoder(stage_cards)
        live_emb = self.card_encoder(live_cards)
        opp_emb = self.card_encoder(opp_cards)

        # 3. Process Zones

        # A. Hand: Flattened embeddings (preserving slot-to-card mapping)
        # We still apply the mask to zero out empty slots
        mask_expanded = hand_mask.unsqueeze(-1).float()
        hand_processed = hand_emb * (1.0 - mask_expanded)
        hand_flat_emb = hand_processed.reshape(batch_size, -1)

        # B. Stage: Positional Encoding
        stage_processed = stage_emb + self.stage_pos_emb
        stage_flat_emb = stage_processed.reshape(batch_size, -1)

        # C. Live: Positional Encoding
        live_processed = live_emb + self.live_pos_emb
        live_flat_emb = live_processed.reshape(batch_size, -1)

        # D. Opponent: Attention + Mean Pool (Strategic summary)
        opp_processed = self.opp_attention(opp_emb, mask=opp_mask)
        opp_mask_expanded = opp_mask.unsqueeze(-1).float()
        opp_processed = opp_processed * (1.0 - opp_mask_expanded)
        opp_sum = opp_processed.sum(dim=1)
        opp_counts = 9.0 - opp_mask.sum(dim=1, keepdim=True).float()
        opp_summary = opp_sum / (opp_counts + 1e-6)

        # 4. Fusion
        combined = torch.cat(
            [
                hand_flat_emb,  # 2048
                stage_flat_emb,  # 384
                live_flat_emb,  # 768
                opp_summary,  # 128
                global_features,  # 64
            ],
            dim=1,
        )

        return self.fusion_net(combined)
