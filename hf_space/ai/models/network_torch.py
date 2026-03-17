"""
PyTorch implementation of Transformer-based AlphaZero network.
Processes the game state as a set of interacting cards (Tokens) rather than a flat vector.
"""

from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

# Import config constants
from .training_config import DROPOUT, HIDDEN_SIZE, N_HEADS, NUM_LAYERS


class Tokenizer(nn.Module):
    """
    Slices the 1200-float input vector into semantic tokens:
    - 1 Global Token (144 features: 20 basic + 124 heuristics/misc)
    - 22 Card Tokens (6 Stage, 6 Live, 10 Hand) - 48 features each
    """

    def __init__(self, d_model: int):
        super().__init__()
        self.d_model = d_model

        self.card_size = 48
        # Global (20) + Tail (1076:1200 = 124) = 144 features
        self.global_size = 144

        # Projections
        self.global_proj = nn.Linear(self.global_size, d_model)
        self.card_proj = nn.Linear(self.card_size, d_model)

        # Zone Embeddings: 0=Global, 1=P0_Stage, 2=P1_Stage, 3=P0_Live, 4=P1_Live, 5=P0_Hand
        self.zone_embedding = nn.Embedding(8, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, 1200)
        batch_size = x.shape[0]

        tokens = []

        # 1. Global Token
        # Basic Globals (0-20) + Tail Heuristics (1076-1200)
        global_feat = torch.cat([x[:, 0:20], x[:, 1076:1200]], dim=1)

        t_global = self.global_proj(global_feat)  # (B, d_model)
        t_global = t_global + self.zone_embedding(torch.zeros(batch_size, dtype=torch.long, device=x.device))
        tokens.append(t_global.unsqueeze(1))

        # 2. Card Tokens helper
        def make_cards(start_idx, count, zone_id):
            card_tokens = []
            for i in range(count):
                s = start_idx + i * 48
                e = s + 48
                c_vec = x[:, s:e]
                c_emb = self.card_proj(c_vec)
                c_emb = c_emb + self.zone_embedding(
                    torch.full((batch_size,), zone_id, dtype=torch.long, device=x.device)
                )
                card_tokens.append(c_emb.unsqueeze(1))
            return card_tokens

        # P0 Stage (Zone 1) - starts at 20
        tokens.extend(make_cards(20, 3, 1))
        # P1 Stage (Zone 2) - starts at 164
        tokens.extend(make_cards(164, 3, 2))
        # P0 Live (Zone 3) - starts at 308
        tokens.extend(make_cards(308, 3, 3))
        # P1 Live (Zone 4) - starts at 452
        tokens.extend(make_cards(452, 3, 4))
        # P0 Hand (Zone 5) - starts at 596
        tokens.extend(make_cards(596, 10, 5))

        # SeqLen = 1 + 3 + 3 + 3 + 3 + 10 = 23
        return torch.cat(tokens, dim=1)


class TransformerCardNet(nn.Module):
    def __init__(self, input_size=1200, action_size=2000):
        super().__init__()

        self.d_model = HIDDEN_SIZE

        # 1. Tokenizer
        self.tokenizer = Tokenizer(self.d_model)

        # 2. Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.d_model, nhead=N_HEADS, dim_feedforward=self.d_model * 4, dropout=DROPOUT, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=NUM_LAYERS)

        # 3. Policy Heads
        self.hand_action_proj = nn.Linear(self.d_model, 6)  # [Play0, Play1, Play2, Energy, Mull, LiveSet]
        self.stage_action_proj = nn.Linear(self.d_model, 10)  # [Ability0..9]
        self.live_action_proj = nn.Linear(self.d_model, 1)  # [SelectSuccess]
        self.global_action_proj = nn.Linear(self.d_model, 10)  # [0:Pass, 1..6:Colors, ... ]

        # Value Heads
        # Win-rate head (Sigmoid)
        self.value_win_head = nn.Sequential(nn.Linear(self.d_model, 128), nn.ReLU(), nn.Linear(128, 1), nn.Sigmoid())
        # Score differential head (Tanh -1..1)
        self.value_score_head = nn.Sequential(nn.Linear(self.d_model, 128), nn.ReLU(), nn.Linear(128, 1), nn.Tanh())
        # Auxiliary Pacing Head (Progress 0..1)
        self.turns_head = nn.Sequential(nn.Linear(self.d_model, 64), nn.ReLU(), nn.Linear(64, 1), nn.Sigmoid())

    def forward(self, x):
        batch_size = x.size(0)
        tokens = self.tokenizer(x)
        encoded = self.transformer(tokens)  # (B, 23, d_model)

        # --- Policy Reconstruction ---
        logits = torch.zeros(batch_size, 2000, device=x.device)

        # Global Actions
        global_tok = encoded[:, 0, :]
        g_logits = self.global_action_proj(global_tok)
        logits[:, 0] = g_logits[:, 0]  # Pass
        logits[:, 580:586] = g_logits[:, 1:7]  # Colors

        # Hand Actions (Tokens 13-22)
        hand_toks = encoded[:, 13:23, :]
        h_logits = self.hand_action_proj(hand_toks)  # (B, 10, 6)
        for i in range(10):
            logits[:, 1 + 3 * i : 1 + 3 * i + 3] = h_logits[:, i, 0:3]
            logits[:, 100 + i] = h_logits[:, i, 3]  # Energy
            logits[:, 300 + i] = h_logits[:, i, 4]  # Mull
            logits[:, 400 + i] = h_logits[:, i, 5]  # LiveSet

        # Stage Actions (Tokens 1-3)
        stage_toks = encoded[:, 1:4, :]
        s_logits = self.stage_action_proj(stage_toks)  # (B, 3, 10)
        for i in range(3):
            logits[:, 200 + 10 * i : 200 + 10 * i + 10] = s_logits[:, i, :]

        # Live Zone Actions (Tokens 7-9)
        live_toks = encoded[:, 7:10, :]
        l_logits = self.live_action_proj(live_toks).squeeze(-1)  # (B, 3)
        logits[:, 600:603] = l_logits

        # --- Value Heads ---
        cls_token = encoded[:, 0, :]
        val_win = self.value_win_head(cls_token)  # (B, 1)
        val_score = self.value_score_head(cls_token)  # (B, 1)
        turns_pred = self.turns_head(cls_token)  # (B, 1)

        return F.softmax(logits, dim=1), val_win, val_score, turns_pred


class TorchNetworkWrapper:
    """Wrapper to interface with MCTS/Training loop"""

    def __init__(self, config=None, device=None, enable_compile=True):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")

        self.net = TransformerCardNet().to(self.device)

        if enable_compile and hasattr(torch, "compile") and "win" not in torch.sys.platform:
            try:
                print("Compiling Transformer with torch.compile...")
                self.net = torch.compile(self.net, mode="reduce-overhead")
            except Exception as e:
                print(f"Compile failed: {e}")

        lr = 0.0003
        self.optimizer = optim.AdamW(self.net.parameters(), lr=lr, weight_decay=1e-4)

    def predict(self, state) -> Tuple[np.ndarray, float]:
        self.net.eval()
        obs = state.get_observation()
        if len(obs) != 1200:
            if len(obs) < 1200:
                obs = obs + [0.0] * (1200 - len(obs))
            else:
                obs = obs[:1200]

        x = torch.tensor(obs, dtype=torch.float32).unsqueeze(0).to(self.device)

        with torch.no_grad():
            p_soft, v_win, v_score, t_pred = self.net(x)

        p = p_soft.cpu().numpy()[0]
        v = v_win.item()  # MCTS typically uses win probability [0,1] or [-1,1]

        # Mask illegal
        legal = state.get_legal_actions()
        masked = p * legal
        sum_p = masked.sum()
        if sum_p > 0:
            masked /= sum_p
        else:
            masked = legal.astype(np.float32) / legal.sum()

        return masked, v

    def train_step(self, obs, target_p, target_v_win, target_v_score, target_turns):
        """
        obs: (B, 1200)
        target_p: (B, 2000)
        target_v_win: (B, 1)
        target_v_score: (B, 1)
        target_turns: (B, 1)
        """
        self.net.train()
        self.optimizer.zero_grad()

        x = torch.tensor(obs, dtype=torch.float32).to(self.device)
        t_p = torch.tensor(target_p, dtype=torch.float32).to(self.device)
        t_w = torch.tensor(target_v_win, dtype=torch.float32).to(self.device)
        t_s = torch.tensor(target_v_score, dtype=torch.float32).to(self.device)
        t_t = torch.tensor(target_turns, dtype=torch.float32).to(self.device)

        p, w, s, t = self.net(x)

        loss_p = -torch.sum(t_p * torch.log(p + 1e-8)) / x.size(0)
        loss_w = F.binary_cross_entropy(w, t_w)
        loss_s = F.mse_loss(s, t_s)
        loss_t = F.mse_loss(t, t_t)

        total_loss = loss_p + loss_w + loss_s + loss_t
        total_loss.backward()
        self.optimizer.step()

        return total_loss.item(), loss_p.item(), loss_w.item(), loss_s.item()

    def save(self, path):
        if hasattr(self.net, "_orig_mod"):
            torch.save(self.net._orig_mod.state_dict(), path)
        else:
            torch.save(self.net.state_dict(), path)

    def load(self, path):
        sd = torch.load(path, map_location=self.device)
        sd = {k.replace("_orig_mod.", ""): v for k, v in sd.items()}
        if hasattr(self.net, "_orig_mod"):
            self.net._orig_mod.load_state_dict(sd)
        else:
            self.net.load_state_dict(sd)
