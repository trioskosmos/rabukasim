from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Optional

import torch
import torch.nn as nn

from alphazero.training.vanilla_action_codec import ACTION_SPACE

DEFAULT_HEURISTIC_WEIGHTS = [1.0] * 17

VANILLA_ACTION_CONTEXT_FEATURES = 8
VANILLA_GLOBAL_FEATURES = 20 + VANILLA_ACTION_CONTEXT_FEATURES
VANILLA_CARD_FEATURES = 13
VANILLA_TOTAL_CARDS = 60
VANILLA_INPUT_DIM = VANILLA_GLOBAL_FEATURES + VANILLA_TOTAL_CARDS * VANILLA_CARD_FEATURES
PHASE_VALUES = (-3, -2, -1, 0, 1, 4, 5, 8, 10)


@dataclass(frozen=True)
class VanillaTransformerConfig:
    input_dim: int = VANILLA_INPUT_DIM
    global_dim: int = VANILLA_GLOBAL_FEATURES
    total_cards: int = VANILLA_TOTAL_CARDS
    card_features: int = VANILLA_CARD_FEATURES
    num_actions: int = ACTION_SPACE
    preset: str = "base"
    embed_dim: int = 192
    num_heads: int = 8
    num_layers: int = 6
    ff_multiplier: int = 4
    dropout: float = 0.1
    summary_dim: int = 384
    value_dim: int = 1

    @classmethod
    def from_preset(cls, preset: str = "base", **overrides) -> "VanillaTransformerConfig":
        preset_name = preset.lower()
        presets = {
            "tiny": dict(embed_dim=96, num_heads=4, num_layers=3, ff_multiplier=3, summary_dim=192, dropout=0.06),
            "small": dict(embed_dim=128, num_heads=8, num_layers=4, ff_multiplier=4, summary_dim=256, dropout=0.08),
            "base": dict(embed_dim=192, num_heads=8, num_layers=6, ff_multiplier=4, summary_dim=384, dropout=0.10),
            "large": dict(embed_dim=256, num_heads=8, num_layers=8, ff_multiplier=4, summary_dim=512, dropout=0.10),
        }
        if preset_name not in presets:
            raise ValueError(f"Unknown vanilla model preset: {preset}")
        return cls(preset=preset_name, **presets[preset_name], **overrides)


def build_vanilla_transformer_config(
    preset: str = "base",
    *,
    embed_dim: Optional[int] = None,
    num_heads: Optional[int] = None,
    num_layers: Optional[int] = None,
    ff_multiplier: Optional[int] = None,
    dropout: Optional[float] = None,
    summary_dim: Optional[int] = None,
    value_dim: Optional[int] = None,
) -> VanillaTransformerConfig:
    config = VanillaTransformerConfig.from_preset(preset)
    overrides = {}
    if embed_dim is not None:
        overrides["embed_dim"] = embed_dim
    if num_heads is not None:
        overrides["num_heads"] = num_heads
    if num_layers is not None:
        overrides["num_layers"] = num_layers
    if ff_multiplier is not None:
        overrides["ff_multiplier"] = ff_multiplier
    if dropout is not None:
        overrides["dropout"] = dropout
    if summary_dim is not None:
        overrides["summary_dim"] = summary_dim
    if value_dim is not None:
        overrides["value_dim"] = value_dim
    return replace(config, **overrides) if overrides else config


def list_vanilla_presets() -> list[dict[str, object]]:
    presets = []
    for preset_name in ("tiny", "small", "base", "large"):
        config = VanillaTransformerConfig.from_preset(preset_name)
        model = HighFidelityAlphaNet(config=config)
        presets.append(
            {
                "preset": preset_name,
                "config": config,
                "parameters": model.parameter_count(),
                "parameters_millions": model.parameter_count_millions(),
            }
        )
    return presets


def choose_vanilla_config_for_budget(
    budget_millions: float,
    *,
    fallback_preset: str = "base",
) -> VanillaTransformerConfig:
    candidates = list_vanilla_presets()
    within_budget = [entry for entry in candidates if entry["parameters_millions"] <= budget_millions]
    if within_budget:
        return within_budget[-1]["config"]

    for entry in candidates:
        if entry["preset"] == fallback_preset:
            return entry["config"]
    return candidates[0]["config"]


class HighFidelityAlphaNet(nn.Module):
    def __init__(
        self,
        input_dim: int = VANILLA_INPUT_DIM,
        num_actions: int = ACTION_SPACE,
        embed_dim: int = 192,
        num_heads: int = 8,
        num_layers: int = 6,
        ff_multiplier: int = 4,
        dropout: float = 0.1,
        summary_dim: int = 384,
        config: Optional[VanillaTransformerConfig] = None,
    ):
        super().__init__()

        self.config = config or VanillaTransformerConfig(
            input_dim=input_dim,
            num_actions=num_actions,
            embed_dim=embed_dim,
            num_heads=num_heads,
            num_layers=num_layers,
            ff_multiplier=ff_multiplier,
            dropout=dropout,
            summary_dim=summary_dim,
        )
        cfg = self.config
        if cfg.global_dim + cfg.total_cards * cfg.card_features != cfg.input_dim:
            raise ValueError(
                "Vanilla net config is inconsistent: "
                f"global_dim={cfg.global_dim}, total_cards={cfg.total_cards}, "
                f"card_features={cfg.card_features}, input_dim={cfg.input_dim}"
            )

        self.cls_token = nn.Parameter(torch.zeros(1, 1, cfg.embed_dim))
        self.card_index_embedding = nn.Embedding(cfg.total_cards, cfg.embed_dim)
        self.zone_embedding = nn.Embedding(8, cfg.embed_dim)
        self.phase_embedding = nn.Embedding(len(PHASE_VALUES) + 1, cfg.embed_dim)
        self.card_type_embedding = nn.Embedding(4, cfg.embed_dim)

        self.global_projection = nn.Sequential(
            nn.Linear(cfg.global_dim, cfg.embed_dim),
            nn.LayerNorm(cfg.embed_dim),
            nn.GELU(),
        )
        self.card_projection = nn.Sequential(
            nn.Linear(cfg.card_features, cfg.embed_dim),
            nn.LayerNorm(cfg.embed_dim),
            nn.GELU(),
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=cfg.embed_dim,
            nhead=cfg.num_heads,
            dim_feedforward=cfg.embed_dim * cfg.ff_multiplier,
            dropout=cfg.dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=cfg.num_layers)
        pooled_dim = cfg.embed_dim * 3
        self.summary = nn.Sequential(
            nn.Linear(pooled_dim, cfg.summary_dim),
            nn.GELU(),
            nn.LayerNorm(cfg.summary_dim),
            nn.Dropout(cfg.dropout),
            nn.Linear(cfg.summary_dim, cfg.summary_dim),
            nn.GELU(),
            nn.LayerNorm(cfg.summary_dim),
        )
        self.pool_gate = nn.Linear(cfg.embed_dim, 1)
        self.policy_head = nn.Sequential(
            nn.Linear(cfg.summary_dim, cfg.summary_dim),
            nn.GELU(),
            nn.LayerNorm(cfg.summary_dim),
            nn.Linear(cfg.summary_dim, cfg.num_actions),
        )
        self.value_head = nn.Sequential(
            nn.Linear(cfg.summary_dim, cfg.summary_dim // 2),
            nn.GELU(),
            nn.LayerNorm(cfg.summary_dim // 2),
            nn.Linear(cfg.summary_dim // 2, cfg.value_dim),
        )
        self.register_buffer("card_positions", torch.arange(cfg.total_cards, dtype=torch.long), persistent=False)
        self.reset_parameters()

    def reset_parameters(self) -> None:
        nn.init.normal_(self.cls_token, mean=0.0, std=0.02)

    def parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())

    def parameter_count_millions(self) -> float:
        return self.parameter_count() / 1_000_000.0

    def describe(self) -> dict[str, object]:
        data = asdict(self.config)
        data["parameters"] = self.parameter_count()
        data["parameters_millions"] = round(self.parameter_count_millions(), 3)
        return data

    def _phase_ids_from_scalar(self, phase_scalar: torch.Tensor) -> torch.Tensor:
        phase_rounded = torch.round(phase_scalar).long()
        phase_ids = torch.full_like(phase_rounded, len(PHASE_VALUES))
        for idx, value in enumerate(PHASE_VALUES):
            phase_ids = torch.where(phase_rounded == value, torch.full_like(phase_ids, idx), phase_ids)
        return phase_ids.clamp_(0, len(PHASE_VALUES))

    def _encode(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        cfg = self.config
        batch_size = x.size(0)
        global_features = x[:, : cfg.global_dim]
        card_features = x[:, cfg.global_dim :].view(batch_size, cfg.total_cards, cfg.card_features)
        zone_ids = torch.round(card_features[:, :, 0] * 10.0).long().clamp_(0, 7)
        card_type_ids = torch.round(card_features[:, :, 1]).long().clamp_(0, 3)
        phase_ids = self._phase_ids_from_scalar(global_features[:, 0])
        valid_mask = card_features.abs().sum(dim=2) > 0

        cls = self.cls_token.expand(batch_size, -1, -1)
        cls = cls + self.global_projection(global_features).unsqueeze(1)
        cls = cls + self.phase_embedding(phase_ids).unsqueeze(1)

        card_tokens = self.card_projection(card_features)
        card_tokens = card_tokens + self.card_index_embedding(self.card_positions).unsqueeze(0)
        card_tokens = card_tokens + self.zone_embedding(zone_ids)
        card_tokens = card_tokens + self.card_type_embedding(card_type_ids)
        tokens = torch.cat([cls, card_tokens], dim=1)
        encoded = self.transformer(tokens)
        return encoded, valid_mask

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None):
        x = x.float()
        encoded, valid_mask = self._encode(x)
        cls_out = encoded[:, 0, :]
        card_tokens = encoded[:, 1:, :]

        token_scores = self.pool_gate(card_tokens).squeeze(-1)
        mask_fill_value = torch.finfo(token_scores.dtype).min
        token_scores = token_scores.masked_fill(~valid_mask, mask_fill_value)
        token_weights = torch.softmax(token_scores, dim=1)
        attn_pool = torch.sum(card_tokens * token_weights.unsqueeze(-1), dim=1)
        valid_counts = valid_mask.sum(dim=1, keepdim=True).clamp_min(1)
        card_mean = torch.sum(card_tokens * valid_mask.unsqueeze(-1), dim=1) / valid_counts
        summary = self.summary(torch.cat([cls_out, attn_pool, card_mean], dim=1))

        policy_logits = self.policy_head(summary)
        if mask is not None:
            policy_mask_value = torch.finfo(policy_logits.dtype).min
            policy_logits = policy_logits.masked_fill(~mask.bool(), policy_mask_value)
        value_outputs = self.value_head(summary)
        return policy_logits, value_outputs

    def predict_batch(self, tensors):
        device = next(self.parameters()).device
        obs_t = torch.as_tensor(tensors, dtype=torch.float32, device=device)
        with torch.inference_mode():
            logits, value_outputs = self.forward(obs_t)
            probs = torch.softmax(logits, dim=1).cpu().numpy().tolist()
            if value_outputs.size(1) == 1:
                win_values = torch.tanh(value_outputs[:, 0]).cpu().numpy().tolist()
            else:
                win_values = torch.softmax(value_outputs, dim=1)[:, 0].cpu().numpy().tolist()
        weights = [DEFAULT_HEURISTIC_WEIGHTS[:] for _ in range(len(tensors))]
        return win_values, probs, weights


VanillaPolicyValueNet = HighFidelityAlphaNet
