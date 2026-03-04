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
ACTION_BASE_HAND_ACTIVATE = 1600
ACTION_BASE_TURN_CHOICE = 5000  # Intercept BEFORE HandChoice range — TurnChoice collision
ACTION_BASE_HAND_CHOICE = 2200
ACTION_BASE_HAND_SELECT = 8200
ACTION_BASE_STAGE = 8300
ACTION_BASE_STAGE_CHOICE = 8600
ACTION_BASE_DISCARD_ACTIVATE = 9300
ACTION_BASE_ENERGY = 10000
ACTION_BASE_CHOICE = 11000
ACTION_BASE_RPS = 20000
ACTION_BASE_RPS_P2 = 21000

NUM_ACTIONS = 22000

# Action type ranges: (start, end_exclusive, type_index)
# IMPORTANT: Ranges are applied in ORDER — LATER entries overwrite earlier ones.
# TurnChoice (5000-5001) must come AFTER HandChoice (which also covers those IDs)
# so TurnChoice wins the overwrite for positions 5000 and 5001.
ACTION_TYPE_RANGES = [
    (ACTION_BASE_PASS, ACTION_BASE_PASS + 1, 0),               # Pass
    (ACTION_BASE_MULLIGAN, ACTION_BASE_MULLIGAN + 60, 1),       # Mulligan
    (ACTION_BASE_LIVESET, ACTION_BASE_LIVESET + 100, 2),        # SetLive
    (ACTION_BASE_MODE, ACTION_BASE_MODE + 100, 3),              # SelectMode
    (ACTION_BASE_COLOR, ACTION_BASE_COLOR + 10, 4),             # SelectColor
    (ACTION_BASE_STAGE_SLOTS, ACTION_BASE_STAGE_SLOTS + 20, 5), # SelectStageSlot
    (ACTION_BASE_HAND, ACTION_BASE_HAND_ACTIVATE, 6),           # PlayMember
    (ACTION_BASE_HAND_ACTIVATE, ACTION_BASE_HAND_CHOICE, 7),    # HandActivate
    (ACTION_BASE_HAND_CHOICE, ACTION_BASE_HAND_SELECT, 8),      # PlayMemberChoice
    # TurnChoice AFTER HandChoice so it overwrites positions 5000/5001.
    # Without this, 5000 → HandChoice sub-idx 2800 (5000-2200). With this → sub-idx 0.
    (ACTION_BASE_TURN_CHOICE, ACTION_BASE_TURN_CHOICE + 2, 17), # TurnChoice (overwrites)
    (ACTION_BASE_HAND_SELECT, ACTION_BASE_STAGE, 9),            # HandSelect (Targets)
    (ACTION_BASE_STAGE, ACTION_BASE_STAGE_CHOICE, 10),          # ActivateMember (Tableau)
    (ACTION_BASE_STAGE_CHOICE, ACTION_BASE_DISCARD_ACTIVATE, 11), # ActivateMemberChoice
    (ACTION_BASE_DISCARD_ACTIVATE, ACTION_BASE_ENERGY, 12),     # DiscardActivate
    (ACTION_BASE_ENERGY, ACTION_BASE_CHOICE, 13),               # SelectEnergy
    (ACTION_BASE_CHOICE, ACTION_BASE_CHOICE + 5000, 14),        # SelectChoice
    (ACTION_BASE_RPS, ACTION_BASE_RPS + 10, 15),                # RPS (P0)
    (ACTION_BASE_RPS_P2, ACTION_BASE_RPS_P2 + 10, 16),          # RPS (P1)
]
NUM_ACTION_TYPES = 18  # 0-16 original + 17 TurnChoice
# Max sub-index cap. All type ranges have meaningful sub-indices <= 100 in practice.
# HandChoice/SelectChoice have larger raw ranges but the action mask enforces
# correctness; the sub-head learns within [0, MAX_SUB_INDEX).
MAX_SUB_INDEX = 100



def build_action_decomposition_table():
    """Pre-compute type_idx and sub_idx for every action_id 0..NUM_ACTIONS.
    Returns: (type_table[NUM_ACTIONS], sub_table[NUM_ACTIONS])

    Sub-index normalization:
    - Most types: sub_idx = action_id - base_start
    - ActivateMember (type 10, base 8300): engine encodes slot*100+ab*10, stride-100.
      We remap to slot*10+ab_idx so max sub_idx = 2*10+9 = 29 (fits in 100).
    - StageChoice (type 11, base 8600): engine encodes slot*100+ab*10+choice.
      We remap to slot*30+ab*10+choice so max = 2*30+9*10+9 = 159 BUT in
      practice slot<3, ab<5, choice<10 -> max = 2*30+4*10+9 = 109. Clamp to 99.
    """
    type_table = np.full(NUM_ACTIONS, -1, dtype=np.int32)
    sub_table = np.zeros(NUM_ACTIONS, dtype=np.int32)

    for start, end, type_idx in ACTION_TYPE_RANGES:
        for aid in range(start, min(end, NUM_ACTIONS)):
            type_table[aid] = type_idx
            raw = aid - start
            if type_idx == 10:
                # ActivateMember: raw = slot_idx*100 + ab_idx*10 -> compress to slot*10+ab
                slot_idx = raw // 100
                ab_idx = (raw % 100) // 10
                sub_table[aid] = min(slot_idx * 10 + ab_idx, 99)
            elif type_idx == 11:
                # StageChoice: raw = slot*100 + ab*10 + choice -> compress to slot*20+ab*5+choice
                slot_idx = raw // 100
                rem = raw % 100
                ab_idx = rem // 10
                choice = rem % 10
                sub_table[aid] = min(slot_idx * 20 + ab_idx * 5 + choice, 99)
            else:
                sub_table[aid] = min(raw, 99)

    return type_table, sub_table


# Pre-compute at module load time (constant, no GPU needed)
ACTION_TYPE_TABLE, ACTION_SUB_TABLE = build_action_decomposition_table()


class AlphaNet(nn.Module):
    """
    AlphaZero v8 — Relational Transformer with Action Branching.

    Input: (Batch, 20500) flat tensor from Rust engine.
    Tensor layout:
        Global(100) + 120 Cards (Entity Vector Size 170)

    Improvements over v7:
        1. Zone-aware positional embeddings (5 zones)
        2. Mixed aggregation (Global token + Mean pool → 512-dim)
        3. Action-branching policy head (type + sub-index, combined additively)
        4. SiLU activations in value head
    """
    def __init__(self,
                 global_dim=100,
                 card_dim=170,
                 num_cards=120,
                 embed_dim=512,
                 num_heads=8,
                 num_layers=4,
                 num_actions=NUM_ACTIONS,
                 num_action_types=NUM_ACTION_TYPES,
                 max_sub_index=100):
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

        # 3. Transformer Backbone (Deep Reasoning)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=embed_dim * 2,
            batch_first=True,
            norm_first=True,
            activation='gelu'
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers, enable_nested_tensor=False)
        

        # 4. Aggregation dimension (Pure CLS Token)
        summary_dim = embed_dim

        # 5. Action-Branching Policy Head
        # Type head: "What kind of action?" (18 types)
        self.policy_type_head = nn.Sequential(
            nn.Linear(summary_dim, embed_dim),
            nn.SiLU(),
            nn.Linear(embed_dim, num_action_types)
        )
        # Dense Sub-Head: replaces the old pointer network.
        # Pointer attention to 121 tokens was broken because sub-indices are
        # compound encodings (e.g. hand_idx*100 + slot*10 + choice), not token positions.
        # A dense MLP produces correct, independent logits for each (type, sub_idx) pair.
        self.sub_head = nn.Sequential(
            nn.Linear(summary_dim, embed_dim),
            nn.SiLU(),
            nn.Linear(embed_dim, num_action_types * max_sub_index)  # (B, 18*100 = 1800)
        )
        
        # Zero-initialize the final policy layers to output uniform distribution initially
        nn.init.zeros_(self.policy_type_head[-1].weight)
        nn.init.zeros_(self.policy_type_head[-1].bias)
        nn.init.zeros_(self.sub_head[-1].weight)
        nn.init.zeros_(self.sub_head[-1].bias)

        # Use the pre-calculated tables from build_action_decomposition_table() 
        # for 100% parity with the engine and training logic.
        self.register_buffer('action_type_lut', torch.from_numpy(ACTION_TYPE_TABLE).long())
        self.register_buffer('action_sub_lut', torch.from_numpy(ACTION_SUB_TABLE).long())

        # 6. Multi-Objective Value Head
        # Output: [Prob (Win/Loss), Momentum (Score Diff), Efficiency (Turns)]
        self.value_head = nn.Sequential(
            nn.Linear(summary_dim, embed_dim),
            nn.SiLU(),
            nn.Linear(embed_dim, embed_dim // 2),
            nn.SiLU(),
            nn.Linear(embed_dim // 2, 3) 
        )

    def forward(self, x, mask=None):
        # x: (Batch, 20500) - Global(100) + 120 * 170
        batch_size = x.size(0)

        # ========================================
        # 1. PARSE THE FLAT TENSOR
        # ========================================
        global_part = x[:, :self.global_dim]  # (Batch, 100)

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
        # 4. STRATEGIC DEEP REASONING (Transformer + GRU)
        # ========================================
        tokens = torch.cat([global_token, card_tokens], dim=1)  # (Batch, 121, 512)
        latent = self.transformer(tokens)  # (Batch, 121, 512)

        # ========================================
        # 5. AGGREGATION (Pure CLS Token)
        # ========================================
        summary = latent[:, 0, :]                  # (Batch, 512)

        # ========================================
        # 6. RELATIONAL ACTION-BRANCHING POLICY
        # ========================================
        type_logits = self.policy_type_head(summary)   # (Batch, num_action_types)
        
        # Dense Sub-Head: (Batch, num_action_types * max_sub_index)
        # e.g. (B, 18*100 = 1800)
        sub_logits = self.sub_head(summary)

        # Reconstruct full policy via additive hierarchical decomposition:
        # policy[a] = type_logit[type_of(a)] + sub_logit[type_of(a), sub_of(a)]
        type_lut = self.action_type_lut  # (NUM_ACTIONS,)
        sub_lut = self.action_sub_lut    # (NUM_ACTIONS,)

        # Clamp -1 types to 0 for indexing, we'll mask them out below
        # IMPORTANT: Also mask out types that are >= num_action_types for this model instance!
        valid_mask = (type_lut >= 0) & (type_lut < self.num_action_types)
        safe_type = type_lut.clamp(min=0, max=self.num_action_types - 1)
        safe_sub = sub_lut.clamp(min=0, max=self.max_sub_index - 1)

        # Hierarchical indexing: (type_idx * 100 + sub_idx)
        # Each action ID maps to a unique (type, sub) pair in the flattened sub-head
        flat_sub_indices = safe_type * self.max_sub_index + safe_sub
        
        type_contrib = type_logits[:, safe_type]      # (Batch, NUM_ACTIONS)
        sub_contrib = sub_logits[:, flat_sub_indices]  # (Batch, NUM_ACTIONS)

        policy = type_contrib + sub_contrib  # (Batch, NUM_ACTIONS)

        # Mask out unmapped action IDs
        policy[:, ~valid_mask] = -1e4

        # Mask illegal actions
        if mask is not None:
            policy = policy.masked_fill(~mask, -1e4)

        # ========================================
        # 7. MULTI-OBJECTIVE VALUE HEAD
        # ========================================
        val_logits = self.value_head(summary)  # (Batch, 3)
        
        # Constraints: 
        # Prob -> Sigmoid [0,1], Momentum -> Tanh [-1, 1], Turns -> Sigmoid [0,1]
        v_prob = torch.sigmoid(val_logits[:, 0:1])
        v_momentum = torch.tanh(val_logits[:, 1:2])
        v_turns = torch.sigmoid(val_logits[:, 2:3])
        
        value = torch.cat([v_prob, v_momentum, v_turns], dim=1) # (Batch, 3)

        return policy, value


    def forward_heads(self, x, mask=None):
        """Like forward() but returns raw (type_logits, sub_logits, value) in compressed space.
        Use this for training — backward stays in (B,18)+(B,1800) space instead of (B,22000).
        """
        batch_size = x.size(0)
        global_part = x[:, :self.global_dim]
        cards_part  = x[:, self.global_dim:].view(batch_size, self.num_cards, self.card_dim)

        card_tokens  = self.card_encoder(cards_part)
        global_token = self.global_encoder(global_part).unsqueeze(1)

        card_zones   = self.zone_embedding(self.card_zone_ids)
        card_tokens  = card_tokens + card_zones.unsqueeze(0)
        global_zone  = self.zone_embedding(self.global_zone_id)
        global_token = global_token + global_zone.unsqueeze(0)

        tokens = torch.cat([global_token, card_tokens], dim=1)
        latent = self.transformer(tokens)
        summary = latent[:, 0, :]

        type_logits = self.policy_type_head(summary)              # (B, 18)
        sub_logits  = self.sub_head(summary)                      # (B, 1800)

        # Value head (same as forward)
        val_logits = self.value_head(summary)
        value = torch.cat([
            torch.sigmoid(val_logits[:, 0:1]),
            torch.tanh(val_logits[:, 1:2]),
            torch.sigmoid(val_logits[:, 2:3]),
        ], dim=1)

        return type_logits, sub_logits, value


def save_model(model, path="alphanet_latest.pt"):
    torch.save(model.state_dict(), path)

def load_model(path, device="cpu"):
    state_dict = torch.load(path, map_location=device)
    
    # Detect head sizes from checkpoint (default to current NUM_ACTION_TYPES=18)
    num_action_types = state_dict.get("policy_type_head.2.weight", torch.zeros(18, 1)).shape[0]
    
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
    dummy_input = torch.randn(8, 20500)  # Global(100) + 120*170
    dummy_mask = torch.ones(8, NUM_ACTIONS, dtype=torch.bool)
    p, v = model(dummy_input, mask=dummy_mask)
    print(f"Policy shape: {p.shape}")  # Expected: [8, 22000]
    print(f"Value shape: {v.shape}")   # Expected: [8, 1]
    print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"Zone embeddings: {model.zone_embedding.weight.shape}")
    print("Smoke test passed!")
