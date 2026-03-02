import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# ============================================================
# ACTION SPACE DECOMPOSITION
# Mirrors engine_rust_src/src/core/generated_constants.rs
# ============================================================
ACTION_BASE_PASS = 0
ACTION_BASE_MULLIGAN = 300
ACTION_BASE_LIVESET = 400
ACTION_BASE_MODE = 500
ACTION_BASE_COLOR = 580
ACTION_BASE_STAGE_SLOTS = 600
ACTION_BASE_HAND = 1000
ACTION_BASE_HAND_CHOICE = 2000
ACTION_BASE_HAND_SELECT = 3000
ACTION_BASE_STAGE = 4000
ACTION_BASE_STAGE_CHOICE = 4300
ACTION_BASE_DISCARD_ACTIVATE = 5000
ACTION_BASE_HAND_ACTIVATE = 5600
ACTION_BASE_ENERGY = 6000
ACTION_BASE_CHOICE = 8000

NUM_ACTIONS = 16384

# Action type ranges: (start, end_exclusive, type_index)
# Type indices 0-14 for categories, used by the branching head
ACTION_TYPE_RANGES = [
    (ACTION_BASE_PASS, ACTION_BASE_PASS + 1, 0),             # Pass
    (ACTION_BASE_MULLIGAN, ACTION_BASE_MULLIGAN + 60, 1),     # Mulligan
    (ACTION_BASE_LIVESET, ACTION_BASE_LIVESET + 100, 2),      # SetLive
    (ACTION_BASE_MODE, ACTION_BASE_MODE + 100, 3),            # SelectMode
    (ACTION_BASE_COLOR, ACTION_BASE_COLOR + 10, 4),           # SelectColor
    (ACTION_BASE_STAGE_SLOTS, ACTION_BASE_STAGE_SLOTS + 20, 5), # SelectStageSlot
    (ACTION_BASE_HAND, ACTION_BASE_HAND_CHOICE, 6),           # PlayMember
    (ACTION_BASE_HAND_CHOICE, ACTION_BASE_HAND_SELECT, 7),    # PlayMemberChoice
    (ACTION_BASE_HAND_SELECT, ACTION_BASE_HAND_SELECT + 1000, 8), # HandSelect
    (ACTION_BASE_STAGE, ACTION_BASE_STAGE_CHOICE, 9),         # ActivateMember
    (ACTION_BASE_STAGE_CHOICE, ACTION_BASE_DISCARD_ACTIVATE, 10), # ActivateMemberChoice
    (ACTION_BASE_DISCARD_ACTIVATE, ACTION_BASE_DISCARD_ACTIVATE + 600, 11), # DiscardActivate
    (ACTION_BASE_HAND_ACTIVATE, ACTION_BASE_HAND_ACTIVATE + 200, 12), # HandActivate
    (ACTION_BASE_ENERGY, ACTION_BASE_ENERGY + 100, 13),       # SelectEnergy
    (ACTION_BASE_CHOICE, ACTION_BASE_CHOICE + 2000, 14),      # SelectChoice
    (10000, 10000 + 10, 15),                                 # RPS (P0)
    (11000, 11000 + 10, 16),                                 # RPS (P1)
]
NUM_ACTION_TYPES = 17
# Practical audit: Most choices use sub-indices 0-10.
# Rare edge cases (hand_idx>10) get clamped; the action mask
# ensures only legal actions are selected regardless.
MAX_SUB_INDEX = 100


def build_action_decomposition_table():
    """Pre-compute type_idx and sub_idx for every action_id 0..16383.
    Returns: (type_table[16384], sub_table[16384])
    """
    type_table = np.full(NUM_ACTIONS, -1, dtype=np.int32)
    sub_table = np.zeros(NUM_ACTIONS, dtype=np.int32)

    for start, end, type_idx in ACTION_TYPE_RANGES:
        for aid in range(start, min(end, NUM_ACTIONS)):
            type_table[aid] = type_idx
            sub_table[aid] = aid - start

    return type_table, sub_table


# Pre-compute at module load time (constant, no GPU needed)
ACTION_TYPE_TABLE, ACTION_SUB_TABLE = build_action_decomposition_table()


class AlphaNet(nn.Module):
    """
    AlphaZero v8 — Relational Transformer with Action Branching.

    Input: (Batch, 3910) flat tensor from Rust engine.
    Tensor layout:
        Global(25) + MyStage(3×160) + OppStage(3×160) + Hand(15×160) + Hist(45) + Lives(3×160)

    Improvements over v7:
        1. Zone-aware positional embeddings (5 zones)
        2. Mixed aggregation (Global token + Mean pool → 512-dim)
        3. Action-branching policy head (type + sub-index, combined additively)
        4. SiLU activations in value head
    """
    def __init__(self,
                 global_dim=25,
                 card_dim=170,
                 num_cards=120,
                 embed_dim=256,
                 num_heads=8,
                 num_layers=6,
                 num_actions=NUM_ACTIONS,
                 num_action_types=NUM_ACTION_TYPES,
                 max_sub_index=MAX_SUB_INDEX):
        super().__init__()

        self.num_cards = num_cards
        self.card_dim = card_dim
        self.global_dim = global_dim
        self.num_actions = num_actions
        self.num_action_types = num_action_types
        self.max_sub_index = max_sub_index

        # Zone layout: 60 entities for Me, 60 for Opponent
        self.num_zones = 3
        zone_ids = [0] * 60 + [1] * 60
        self.register_buffer('card_zone_ids', torch.tensor(zone_ids, dtype=torch.long))
        self.register_buffer('global_zone_id', torch.tensor([2], dtype=torch.long))

        # 1. Feature Encoders
        self.card_encoder = nn.Sequential(
            nn.LayerNorm(card_dim),
            nn.Linear(card_dim, embed_dim),
            nn.SiLU(),
            nn.Linear(embed_dim, embed_dim),
            nn.LayerNorm(embed_dim)
        )

        self.global_encoder = nn.Sequential(
            nn.LayerNorm(global_dim),
            nn.Linear(global_dim, embed_dim),
            nn.SiLU(),
            nn.Linear(embed_dim, embed_dim),
            nn.LayerNorm(embed_dim)
        )

        # 2. Zone-Aware Positional Embeddings
        self.zone_embedding = nn.Embedding(self.num_zones, embed_dim)

        # 3. Transformer Backbone
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=embed_dim * 2,
            batch_first=True,
            norm_first=True,
            activation='gelu'
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # 4. Mixed Aggregation dimension: embed_dim (global) + embed_dim (mean) = 2*embed_dim
        summary_dim = embed_dim * 2

        # 5. Action-Branching Policy Head
        # Type head: "What kind of action?" (15 types)
        self.policy_type_head = nn.Sequential(
            nn.Linear(summary_dim, embed_dim),
            nn.SiLU(),
            nn.Linear(embed_dim, num_action_types)
        )
        # Sub-index head: "Which specific card/slot?" (2000 sub-indices)
        self.policy_sub_head = nn.Sequential(
            nn.Linear(summary_dim, embed_dim),
            nn.SiLU(),
            nn.Linear(embed_dim, max_sub_index)
        )

        if num_action_types > 15:
            # We are in V8 with RPS support
            ranges = ACTION_TYPE_RANGES
        else:
            # Legacy V7 or early V8
            ranges = ACTION_TYPE_RANGES[:15]
            
        type_table = np.full(NUM_ACTIONS, -1, dtype=np.int32)
        sub_table = np.zeros(NUM_ACTIONS, dtype=np.int32)
        for start, end, t_idx in ranges:
            for aid in range(start, min(end, NUM_ACTIONS)):
                type_table[aid] = t_idx
                sub_table[aid] = aid - start

        self.register_buffer('action_type_lut', torch.from_numpy(type_table).long())
        self.register_buffer('action_sub_lut', torch.from_numpy(sub_table).long())

        # 6. Value Head (SiLU -> Tanh)
        self.value_head = nn.Sequential(
            nn.Linear(summary_dim, embed_dim),
            nn.SiLU(),
            nn.Linear(embed_dim, embed_dim // 2),
            nn.SiLU(),
            nn.Linear(embed_dim // 2, 1),
            nn.Tanh()
        )

    def forward(self, x, mask=None):
        # x: (Batch, 20425) - Global(25) + 120 * 170
        batch_size = x.size(0)

        # ========================================
        # 1. PARSE THE FLAT TENSOR
        # ========================================
        global_part = x[:, :self.global_dim]  # (Batch, 25)

        cards_start = self.global_dim
        cards_part = x[:, cards_start:]  # (Batch, 20400)

        cards_part = cards_part.view(batch_size, self.num_cards, self.card_dim)  # (Batch, 120, 170)

        # ========================================
        # 2. ENCODE TOKENS
        # ========================================
        card_tokens = self.card_encoder(cards_part)  # (Batch, 120, 256)
        global_token = self.global_encoder(global_part).unsqueeze(1)  # (Batch, 1, 256)

        # ========================================
        # 3. ADD ZONE EMBEDDINGS
        # ========================================
        # Card zone embeddings: zones 0-1
        card_zones = self.zone_embedding(self.card_zone_ids)  # (120, 256)
        card_tokens = card_tokens + card_zones.unsqueeze(0)   # Broadcast over batch

        # Global token gets zone 2 (pre-registered buffer)
        global_zone = self.zone_embedding(self.global_zone_id)  # (1, 256)
        global_token = global_token + global_zone.unsqueeze(0)

        # ========================================
        # 4. TRANSFORMER
        # ========================================
        tokens = torch.cat([global_token, card_tokens], dim=1)  # (Batch, 121, 256)
        latent = self.transformer(tokens)  # (Batch, 121, 256)

        # ========================================
        # 5. MIXED AGGREGATION
        # ========================================
        global_summary = latent[:, 0, :]           # (Batch, 256)
        mean_summary = latent.mean(dim=1)          # (Batch, 256)
        summary = torch.cat([global_summary, mean_summary], dim=1)  # (Batch, 512)

        # ========================================
        # 6. ACTION-BRANCHING POLICY
        # ========================================
        type_logits = self.policy_type_head(summary)   # (Batch, 15)
        sub_logits = self.policy_sub_head(summary)     # (Batch, 2000)

        # Reconstruct full 16384-dim policy via additive decomposition:
        # policy[a] = type_logit[type_of(a)] + sub_logit[sub_of(a)]
        # For unmapped actions (type=-1), they get 0 from both heads
        type_lut = self.action_type_lut  # (16384,)
        sub_lut = self.action_sub_lut    # (16384,)

        # Clamp -1 types to 0 for indexing, we'll mask them out below
        # IMPORTANT: Also mask out types that are >= num_action_types for this model instance!
        valid_mask = (type_lut >= 0) & (type_lut < self.num_action_types)
        safe_type = type_lut.clamp(min=0, max=self.num_action_types - 1)
        safe_sub = sub_lut.clamp(min=0, max=self.max_sub_index - 1)

        # Gather: (Batch, 16384) from (Batch, num_action_types) and (Batch, 2000)
        # Note: If the checkpoint has fewer types than current code, 
        # we index into type_logits which will match the checkpoint size.
        type_contrib = type_logits[:, safe_type]  # (Batch, 16384)
        sub_contrib = sub_logits[:, safe_sub]     # (Batch, 16384)

        policy = type_contrib + sub_contrib  # (Batch, 16384)

        # Mask out unmapped action IDs
        policy[:, ~valid_mask] = -1e9

        # Mask illegal actions
        if mask is not None:
            policy = policy.masked_fill(~mask, -1e9)

        # ========================================
        # 7. VALUE HEAD
        # ========================================
        value = self.value_head(summary)  # (Batch, 1)

        return policy, value


def save_model(model, path="alphanet_latest.pt"):
    torch.save(model.state_dict(), path)

def load_model(path, device="cpu"):
    state_dict = torch.load(path, map_location=device)
    
    # Detect head sizes from checkpoint
    num_action_types = state_dict.get("policy_type_head.2.weight", torch.zeros(15, 1)).shape[0]
    
    model = AlphaNet(num_action_types=num_action_types).to(device)
    
    # Check for architecture mismatch (v7 vs v8)
    if "global_zone_id" not in state_dict:
        state_dict["global_zone_id"] = torch.tensor([4], dtype=torch.long)
    if "card_zone_ids" not in state_dict:
        zone_ids = ([0] * 3 + [1] * 3 + [2] * 15 + [3] * 3)
        state_dict["card_zone_ids"] = torch.tensor(zone_ids, dtype=torch.long)

    model.load_state_dict(state_dict, strict=False)
    model.eval()
    return model

if __name__ == "__main__":
    # Smoke test dimensions
    model = AlphaNet()
    dummy_input = torch.randn(8, 20425)  # Global(25) + 120*170
    dummy_mask = torch.ones(8, 16384, dtype=torch.bool)
    p, v = model(dummy_input, mask=dummy_mask)
    print(f"Policy shape: {p.shape}")  # Expected: [8, 16384]
    print(f"Value shape: {v.shape}")   # Expected: [8, 1]
    print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"Zone embeddings: {model.zone_embedding.weight.shape}")
    print("Smoke test passed!")
