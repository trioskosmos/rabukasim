import numpy as np
import torch
import torch.nn as nn

# ============================================================
# CARD-CENTRIC + SLOT-AWARE ACTION SPACE (248 dims)
# ============================================================
# Hierarchy: Phase actions < Generic cards < Slot-specific cards
#
# Actions indexed by initial_deck position + target slot:
# 0: Pass
# 1-6: Mulligan Toggles (hand[0-5])
# 7: Confirm/Done
# 8-67: Generic card play [0-59]
#       - During live phase: play to live zone
#       - During main phase: auto-select best slot (baton pass optimization)
# 68-127: Play card [0-59] to SLOT 0 during main phase
# 128-187: Play card [0-59] to SLOT 1 during main phase
# 188-247: Play card [0-59] to SLOT 2 during main phase
# 248-250: Targeting slot [0-2]
# 251-255: Hand select [0-4]
#
# Masking:
#   Main phase: 0, 8-247 (generic + all slot-specific)
#   Live phase: 0, 8-67 (pass + generic only)
#   Mulligan: 1-7 (toggles + confirm)

NUM_ACTIONS = 256

ACTION_BASE_PASS = 0
ACTION_BASE_MULLIGAN = 300
ACTION_BASE_LIVESET = 400
ACTION_BASE_HAND = 1000


def build_vanilla_action_table():
    """Maps engine action IDs to 128 buckets."""
    # We create a lookup table for all 22k actions
    type_table = np.full(22000, -1, dtype=np.int32)

    # 0: Pass
    type_table[ACTION_BASE_PASS] = 0

    # 1-6: Mulligan (Hand slots 0-5)
    for i in range(6):
        aid = ACTION_BASE_MULLIGAN + i
        if aid < 22000:
            type_table[aid] = 1 + i

    # 7: Confirm (Typical ID for Done/Confirm is in the 11000 range)
    type_table[11000] = 7

    # Note: In a REAL environment, we'd need a mapping from (HandIndex -> DeckIndex)
    # to correctly populate Play Member (8-67).
    # For a smoke test, we just set the ranges.

    return type_table


ACTION_MAP = build_vanilla_action_table()


class HighFidelityAlphaNet(nn.Module):
    def __init__(self, input_dim=800, num_actions=256, embed_dim=256, num_heads=4, num_layers=6):
        super().__init__()

        self.input_dim = input_dim
        self.num_actions = num_actions

        # Encoder: Project card features and global features
        self.feature_encoder = nn.Linear(13, embed_dim)
        self.global_encoder = nn.Linear(20, embed_dim)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim, nhead=num_heads, dim_feedforward=embed_dim * 2, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.policy_head = nn.Linear(embed_dim, num_actions)
        self.value_head = nn.Linear(embed_dim, 1)

        self.register_buffer("action_map", torch.from_numpy(ACTION_MAP).long())

    def predict_batch(self, tensors):
        """
        AlphaZero evaluation hook for Rust MCTS.
        Expected output: (values: List[f32], policies: List[List[f32]], weights: List[List[f32]])
        """
        import torch

        device = next(self.parameters()).device

        # tensors is a list of lists from Rust
        obs_t = torch.tensor(tensors, dtype=torch.float32).to(device)

        with torch.no_grad():
            # No mask available here easily, so we compute raw logits
            # Rust side handles masking if needed, or PUCT takes care of it
            logits, value = self.forward(obs_t)

            # Policy softmax
            probs = torch.softmax(logits, dim=1).cpu().numpy().tolist()
            values = value.cpu().numpy().flatten().tolist()

            # Weights (HeuristicConfig) - currently just default placeholders
            # and scaling_factor as last element (index 16)
            dummy_weights = [[1.0] * 17 for _ in range(len(tensors))]

        return values, probs, dummy_weights

    def forward(self, x, mask=None):
        # x: (Batch, input_dim)
        batch_size = x.size(0)

        # New High-Fi (800) vs Old High-Fi (791) logic
        global_dim = self.input_dim - (60 * 13)
        global_part = x[:, :global_dim]  # (B, global_dim)
        cards_part = x[:, global_dim:].view(batch_size, 60, 13)  # (B, 60, 13)

        # We need a linear layer that matches the global_dim
        # During __init__, we set global_encoder = nn.Linear(20, embed_dim)
        # For benchmarking 791, we'd need to re-init this, or just pad.
        # Let's just padding the global part if it's smaller than the expected 20.

        if global_dim < 20:
            padded_global = torch.zeros(batch_size, 20, device=x.device)
            padded_global[:, :global_dim] = global_part
            global_part = padded_global

        global_token = self.global_encoder(global_part).unsqueeze(1)  # (B, 1, E)
        card_tokens = self.feature_encoder(cards_part)  # (B, 60, E)

        tokens = torch.cat([global_token, card_tokens], dim=1)  # (B, 61, E)
        latent = self.transformer(tokens)

        summary = latent[:, 0, :]  # Use global token as summary

        policy_logits = self.policy_head(summary)  # (B, 64)
        value = torch.sigmoid(self.value_head(summary))

        return policy_logits, value


if __name__ == "__main__":
    model = HighFidelityAlphaNet(input_dim=800, num_actions=64)
    dummy_input = torch.randn(2, 800)
    p, v = model(dummy_input)
    print(f"Policy: {p.shape}, Value: {v.shape}")
    print(f"Total parameters: {sum(p.numel() for p in model.parameters()):,}")
    print("HighFidelityAlphaNet (800x64) smoke test passed!")
