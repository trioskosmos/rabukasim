from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Optional

import torch
import torch.nn as nn

from alphazero.training.vanilla_action_codec import ACTION_SPACE
from alphazero.training.vanilla_observation import CARD_FEATURES, GLOBAL_FEATURES, MAX_INITIAL_DECK, OBS_DIM

DEFAULT_HEURISTIC_WEIGHTS = [1.0] * 17


@dataclass(frozen=True)
class VanillaTransformerConfig:
    input_dim: int = OBS_DIM
    global_dim: int = GLOBAL_FEATURES
    total_cards: int = MAX_INITIAL_DECK
    card_features: int = CARD_FEATURES
    num_actions: int = ACTION_SPACE
    preset: str = "small"
    embed_dim: int = 128
    num_heads: int = 8
    num_layers: int = 4
    ff_multiplier: int = 4
    dropout: float = 0.1
    summary_dim: int = 256

    @classmethod
    def from_preset(cls, preset: str = "small", **overrides) -> "VanillaTransformerConfig":
        preset_name = preset.lower()
        presets = {
            "tiny": dict(embed_dim=96, num_heads=4, num_layers=3, ff_multiplier=3, summary_dim=192, dropout=0.08),
            "small": dict(embed_dim=128, num_heads=8, num_layers=4, ff_multiplier=4, summary_dim=256, dropout=0.10),
            "base": dict(embed_dim=160, num_heads=8, num_layers=6, ff_multiplier=4, summary_dim=320, dropout=0.10),
            "large": dict(embed_dim=192, num_heads=8, num_layers=8, ff_multiplier=4, summary_dim=384, dropout=0.12),
        }
        if preset_name not in presets:
            raise ValueError(f"Unknown vanilla model preset: {preset}")
        return cls(preset=preset_name, **presets[preset_name], **overrides)


def build_vanilla_transformer_config(
    preset: str = "small",
    *,
    embed_dim: Optional[int] = None,
    num_heads: Optional[int] = None,
    num_layers: Optional[int] = None,
    ff_multiplier: Optional[int] = None,
    dropout: Optional[float] = None,
    summary_dim: Optional[int] = None,
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
    return replace(config, **overrides) if overrides else config


def list_vanilla_presets() -> list[dict]:
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
    fallback_preset: str = "small",
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
    """
        Compact masked transformer for the structured abilityless vanilla tensor.

    The model is intentionally parameter-budgeted so it can handle:
    - CPU inference inside self-play workers
    - GPU training from large overnight replay buffers
        - masked compact policy outputs tailored to abilityless game flow
    """

    def __init__(
        self,
        input_dim: int = OBS_DIM,
        num_actions: int = ACTION_SPACE,
        embed_dim: int = 128,
        num_heads: int = 8,
        num_layers: int = 4,
        ff_multiplier: int = 4,
        dropout: float = 0.1,
        summary_dim: int = 256,
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
        if cfg.input_dim != OBS_DIM:
            raise ValueError(f"Vanilla net expects input_dim={OBS_DIM}, got {cfg.input_dim}")

        self.cls_token = nn.Parameter(torch.zeros(1, 1, cfg.embed_dim))
        self.card_index_embedding = nn.Embedding(cfg.total_cards, cfg.embed_dim)
        self.zone_embedding = nn.Embedding(8, cfg.embed_dim)

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
        self.policy_head = nn.Linear(cfg.summary_dim, cfg.num_actions)
        self.value_head = nn.Sequential(
            nn.Linear(cfg.summary_dim, cfg.summary_dim // 2),
            nn.GELU(),
            nn.Linear(cfg.summary_dim // 2, 3),
        )

        self.register_buffer("card_positions", torch.arange(cfg.total_cards, dtype=torch.long), persistent=False)
        self.reset_parameters()

    def reset_parameters(self) -> None:
        nn.init.normal_(self.cls_token, mean=0.0, std=0.02)

    def parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())

    def parameter_count_millions(self) -> float:
        return self.parameter_count() / 1_000_000.0

    def describe(self) -> dict:
        data = asdict(self.config)
        data["parameters"] = self.parameter_count()
        data["parameters_millions"] = round(self.parameter_count_millions(), 3)
        return data

    def _encode(self, x: torch.Tensor) -> torch.Tensor:
        cfg = self.config
        batch_size = x.size(0)

        global_features = x[:, : cfg.global_dim]
        card_features = x[:, cfg.global_dim :].view(batch_size, cfg.total_cards, cfg.card_features)
        zone_ids = torch.round(card_features[:, :, 0] * 7.0).long().clamp_(0, 7)

        global_token = self.global_projection(global_features).unsqueeze(1)
        cls = self.cls_token.expand(batch_size, -1, -1) + global_token

        card_tokens = self.card_projection(card_features)
        card_tokens = card_tokens + self.card_index_embedding(self.card_positions).unsqueeze(0)
        card_tokens = card_tokens + self.zone_embedding(zone_ids)

        tokens = torch.cat([cls, card_tokens], dim=1)
        return self.transformer(tokens)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None):
        x = x.float()
        encoded = self._encode(x)

        cls_out = encoded[:, 0, :]
        card_tokens = encoded[:, 1:, :]
        card_mean = card_tokens.mean(dim=1)
        card_max = card_tokens.max(dim=1).values
        summary = self.summary(torch.cat([cls_out, card_mean, card_max], dim=1))

        policy_logits = self.policy_head(summary)
        if mask is not None:
            policy_logits = policy_logits.masked_fill(~mask.bool(), -1e9)

        value_outputs = self.value_head(summary)
        return policy_logits, value_outputs

    def predict_batch(self, tensors):
        device = next(self.parameters()).device
        obs_t = torch.tensor(tensors, dtype=torch.float32, device=device)

        with torch.no_grad():
            policy_logits, value_outputs = self.forward(obs_t)
            probs = torch.softmax(policy_logits, dim=1).cpu().numpy().tolist()
            win_values = torch.sigmoid(value_outputs[:, 0]).cpu().numpy().tolist()

        weights = [DEFAULT_HEURISTIC_WEIGHTS[:] for _ in range(len(tensors))]
        return win_values, probs, weights


VanillaPolicyValueNet = HighFidelityAlphaNet


if __name__ == "__main__":
    for preset_name in ("tiny", "small", "base"):
        cfg = VanillaTransformerConfig.from_preset(preset_name)
        model = HighFidelityAlphaNet(config=cfg)
        dummy_input = torch.randn(2, OBS_DIM)
        dummy_mask = torch.ones(2, ACTION_SPACE, dtype=torch.bool)
        policy_logits, values = model(dummy_input, dummy_mask)
        print(f"[{preset_name}] policy={tuple(policy_logits.shape)} value={tuple(values.shape)} params={model.parameter_count():,}")