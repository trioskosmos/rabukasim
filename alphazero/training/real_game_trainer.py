from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Sequence

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from alphazero.training.action_features import ACTION_FEATURE_DIM
from alphazero.training.disk_replay import DiskReplayBuffer, DiskReplaySample
from alphazero.training.real_game_env import RealGameEnv, RealGameEnvConfig, make_real_game_env
from alphazero.training.strategic_evaluation import (
    StateStrategicEvaluation,
    evaluate_move_strategic_value,
    evaluate_state_strategic_value,
    live_card_fit_score,
)


@dataclass(frozen=True)
class RealGameTrainerConfig:
    seed: int = 0
    device: str = "cuda"
    episodes: int = 64
    eval_games: int = 16
    updates_per_episode: int = 4
    batch_size: int = 32
    learning_rate: float = 3e-4
    weight_decay: float = 1e-4
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_turns: int = 10
    hidden_dim: int = 256
    replay_size: int | None = None
    replay_buffer_capacity: int = 4096
    replay_buffer_dir: str = "replay/real_game_agent"
    replay_buffer_max_candidates: int = 128
    epsilon_start: float = 0.35
    epsilon_end: float = 0.05
    temperature_start: float = 1.25
    temperature_end: float = 0.85
    log_every_episodes: int = 1
    self_play_use_model: bool = False
    parallel_self_play_games: int = 1
    cpu_search_sims: int = 16
    cpu_search_depth: int = 2
    cpu_search_branch_factor: int = 3
    save_interval_seconds: int = 300
    checkpoint_path: str = "checkpoints/real_game_agent.pt"

    def __post_init__(self) -> None:
        if self.replay_size is not None:
            object.__setattr__(self, "replay_buffer_capacity", max(1, int(self.replay_size)))


STATE_CONTEXT_DIM = 26


@dataclass(slots=True)
class TrajectoryStep:
    obs: np.ndarray
    state_context: np.ndarray
    candidate_features: np.ndarray
    policy_target: np.ndarray
    candidate_utility_targets: np.ndarray
    action_index: int
    player: int
    clearability_target: float = 0.0
    utility_target: float = 0.0
    reward: float = 0.0


class CandidatePolicyValueNet(nn.Module):
    def __init__(self, obs_dim: int, state_context_dim: int, candidate_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.obs_encoder = nn.Sequential(
            nn.LayerNorm(obs_dim),
            nn.Linear(obs_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.context_encoder = nn.Sequential(
            nn.LayerNorm(state_context_dim),
            nn.Linear(state_context_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.candidate_encoder = nn.Sequential(
            nn.LayerNorm(candidate_dim),
            nn.Linear(candidate_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.token_mixer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=hidden_dim,
                nhead=4,
                dim_feedforward=hidden_dim * 4,
                dropout=0.05,
                activation="gelu",
                batch_first=True,
                norm_first=False,
            ),
            num_layers=2,
            enable_nested_tensor=False,
        )
        self.policy_head = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
        )
        self.prompt_head = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 8),
        )
        self.family_head = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 9),
        )
        self.clearability_head = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
        )
        self.utility_head = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
        )
        self.move_utility_head = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
        )
        self.value_head = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(
        self,
        obs_batch: torch.Tensor,
        state_context_batch: torch.Tensor,
        candidate_batch: torch.Tensor,
        candidate_mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        obs_state = self.obs_encoder(obs_batch.float())
        ctx_state = self.context_encoder(state_context_batch.float())
        state = 0.5 * obs_state + 0.5 * ctx_state
        cand = self.candidate_encoder(candidate_batch.float())
        tokens = torch.cat([state.unsqueeze(1), cand], dim=1)
        key_padding_mask = None
        if candidate_mask is not None:
            key_padding_mask = torch.cat(
                [
                    torch.zeros((candidate_mask.shape[0], 1), dtype=torch.bool, device=candidate_mask.device),
                    ~candidate_mask.bool(),
                ],
                dim=1,
            )
        mixed = self.token_mixer(tokens, src_key_padding_mask=key_padding_mask)
        state_token = mixed[:, 0, :]
        cand_tokens = mixed[:, 1:, :]
        logits = self.policy_head(cand_tokens).squeeze(-1)
        if candidate_mask is not None:
            logits = logits.masked_fill(~candidate_mask.bool(), torch.finfo(logits.dtype).min)
        prompt_logits = self.prompt_head(state_token)
        value = self.value_head(state_token).squeeze(-1)
        clearability = self.clearability_head(state_token).squeeze(-1)
        utility = self.utility_head(state_token).squeeze(-1)
        move_utility = self.move_utility_head(cand_tokens).squeeze(-1)
        return logits, value, prompt_logits, clearability, utility, move_utility, mixed


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _linear_schedule(start: float, end: float, step: int, total: int) -> float:
    if total <= 0:
        return float(end)
    ratio = max(0.0, min(1.0, step / float(total)))
    return float(start + (end - start) * ratio)


def _softmax_distribution(scores: Sequence[float], temperature: float) -> np.ndarray:
    values = np.asarray(scores, dtype=np.float32)
    if values.size == 0:
        return np.zeros((0,), dtype=np.float32)
    temp = max(float(temperature), 1e-6)
    shifted = values - float(np.max(values))
    scaled = shifted / temp
    exp = np.exp(np.clip(scaled, -50.0, 50.0))
    total = float(np.sum(exp))
    if not np.isfinite(total) or total <= 0.0:
        return np.full(values.shape, 1.0 / float(values.size), dtype=np.float32)
    return (exp / total).astype(np.float32)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_len(value: Any) -> int:
    try:
        return len(value)
    except TypeError:
        return 0


def _prompt_category(choice_type: str) -> int:
    normalized = choice_type.strip().upper()
    if not normalized:
        return 0
    if "OPTIONAL" in normalized:
        return 1
    if "MODE" in normalized or "SELECT_MODE" in normalized or "CHOOSE" in normalized:
        return 2
    if "TARGET" in normalized or "MEMBER" in normalized or "STAGE" in normalized or "LIVE" in normalized:
        return 3
    if "DISCARD" in normalized:
        return 4
    if "LOOK" in normalized or "ORDER" in normalized:
        return 5
    if "ENERGY" in normalized or "RESOURCE" in normalized or "PAY" in normalized:
        return 6
    return 7


def _state_context_from_info(
    info: dict[str, Any],
    card_lookup: dict[int, dict[str, Any]] | None = None,
    max_turns: int = 10,
) -> np.ndarray:
    state = dict(info.get("state_dict", {}) or {})
    players = list(state.get("players", []))
    current_player = _safe_int(info.get("current_player", state.get("current_player", 0)), 0)
    opponent = 1 - current_player if current_player in (0, 1) else 0
    player = players[current_player] if current_player < len(players) else {}
    opp = players[opponent] if opponent < len(players) else {}

    interaction_stack = list(state.get("interaction_stack", []))
    pending_choice_type = str(state.get("pending_choice_type", "") or "")
    if not pending_choice_type and interaction_stack:
        top = interaction_stack[-1]
        if isinstance(top, dict):
            pending_choice_type = str(top.get("choice_type", "") or top.get("choice", "") or "")

    context = np.zeros(STATE_CONTEXT_DIM, dtype=np.float32)
    turn = _safe_int(info.get("turn", state.get("turn", 0)), 0)
    phase = _safe_int(info.get("phase", state.get("phase", 0)), 0)
    score = _safe_int(player.get("score", 0), 0)
    opp_score = _safe_int(opp.get("score", 0), 0)
    hand = _safe_len(player.get("hand", []))
    opp_hand = _safe_len(opp.get("hand", []))
    stage = sum(1 for cid in player.get("stage", []) if int(cid) >= 0)
    opp_stage = sum(1 for cid in opp.get("stage", []) if int(cid) >= 0)
    live_zone = sum(1 for cid in player.get("live_zone", []) if int(cid) >= 0)
    opp_live = sum(1 for cid in opp.get("live_zone", []) if int(cid) >= 0)
    discard = _safe_len(player.get("discard", []))
    opp_discard = _safe_len(opp.get("discard", []))
    energy = _safe_len(player.get("energy_zone", []))
    opp_energy = _safe_len(opp.get("energy_zone", []))
    legal_count = _safe_len(info.get("legal_actions", []))
    prompt_cat = _prompt_category(pending_choice_type)
    prompt_present = 1.0 if prompt_cat else 0.0
    optional_prompt = 1.0 if "OPTIONAL" in pending_choice_type.upper() else 0.0

    context[0] = min(float(turn) / 20.0, 1.0)
    context[1] = np.clip((float(phase) + 10.0) / 20.0, 0.0, 1.0)
    context[2] = float(current_player)
    context[3] = 1.0 if bool(info.get("winner", -1) != -1) else 0.0
    context[4] = min(float(legal_count) / 20.0, 1.0)
    context[5] = min(float(score) / 20.0, 1.0)
    context[6] = min(float(opp_score) / 20.0, 1.0)
    context[7] = np.clip(float(score - opp_score) / 20.0, -1.0, 1.0)
    context[8] = min(float(hand) / 20.0, 1.0)
    context[9] = min(float(opp_hand) / 20.0, 1.0)
    context[10] = np.clip(float(hand - opp_hand) / 20.0, -1.0, 1.0)
    context[11] = min(float(stage) / 3.0, 1.0)
    context[12] = min(float(opp_stage) / 3.0, 1.0)
    context[13] = np.clip(float(stage - opp_stage) / 3.0, -1.0, 1.0)
    context[14] = min(float(live_zone) / 12.0, 1.0)
    context[15] = min(float(opp_live) / 12.0, 1.0)
    context[16] = min(float(discard) / 60.0, 1.0)
    context[17] = min(float(opp_discard) / 60.0, 1.0)
    context[18] = min(float(energy) / 12.0, 1.0)
    context[19] = min(float(opp_energy) / 12.0, 1.0)
    context[20] = prompt_present
    context[21] = optional_prompt
    context[22] = min(float(prompt_cat) / 7.0, 1.0)
    context[23] = min(float(_safe_int(state.get("trigger_depth", 0), 0)) / 10.0, 1.0)
    if card_lookup is not None:
        state_eval = evaluate_state_strategic_value(state, current_player, card_lookup, max_turns=max_turns)
        context[24] = float(state_eval.clearability)
        context[25] = float(state_eval.strategic_utility)
    return context


def _choose_candidate(
    logits: torch.Tensor,
    temperature: float,
    epsilon: float,
    rng: random.Random,
) -> int:
    if logits.numel() == 0:
        return 0
    if rng.random() < float(epsilon):
        return int(rng.randrange(int(logits.numel())))
    scaled = logits / max(float(temperature), 1e-6)
    probs = torch.softmax(scaled, dim=-1)
    if torch.isnan(probs).any() or float(probs.sum()) <= 0:
        return int(torch.argmax(logits).item())
    return int(torch.multinomial(probs, 1).item())


def _pad_batch(
    steps: Sequence[TrajectoryStep],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    if not steps:
        raise ValueError("Cannot build a batch from zero steps")

    obs = torch.from_numpy(np.stack([step.obs for step in steps]).astype(np.float32))
    max_candidates = max(step.candidate_features.shape[0] for step in steps)
    candidate_dim = steps[0].candidate_features.shape[1] if steps[0].candidate_features.size else ACTION_FEATURE_DIM
    candidate_batch = torch.zeros((len(steps), max_candidates, candidate_dim), dtype=torch.float32)
    candidate_mask = torch.zeros((len(steps), max_candidates), dtype=torch.bool)
    action_index = torch.zeros((len(steps),), dtype=torch.long)
    value_target = torch.zeros((len(steps),), dtype=torch.float32)

    for row, step in enumerate(steps):
        cand = torch.from_numpy(np.asarray(step.candidate_features, dtype=np.float32))
        if cand.numel() > 0:
            candidate_batch[row, : cand.shape[0], : cand.shape[1]] = cand
            candidate_mask[row, : cand.shape[0]] = True
        action_index[row] = int(step.action_index)

    return obs, candidate_batch, candidate_mask, action_index, value_target


class RealGameTrainer:
    def __init__(self, config: RealGameTrainerConfig):
        self.config = config
        self.device = torch.device(config.device)
        if self.device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available in this Torch runtime")
        self.rng = random.Random(config.seed)
        _seed_everything(config.seed)
        self.env = make_real_game_env(
            RealGameEnvConfig(seed=config.seed, max_turns=config.max_turns),
            max_turns=config.max_turns,
        )
        self.engine = self.env._engine
        obs, info = self.env.reset(seed=config.seed)
        candidate_features = np.asarray(info["candidate_action_features"], dtype=np.float32)
        state_context = _state_context_from_info(info, self.env.card_lookup, config.max_turns)
        self.model = CandidatePolicyValueNet(
            obs.shape[0],
            state_context.shape[0],
            candidate_features.shape[1],
            config.hidden_dim,
        ).to(self.device)
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )
        self.scaler = torch.amp.GradScaler("cuda", enabled=self.device.type == "cuda")
        self.replay = DiskReplayBuffer(
            config.replay_buffer_dir,
            capacity=config.replay_buffer_capacity,
            obs_dim=obs.shape[0],
            state_context_dim=state_context.shape[0],
            candidate_dim=candidate_features.shape[1],
            max_candidates=config.replay_buffer_max_candidates,
        )
        self._resume_from_checkpoint(config.checkpoint_path)

    def _resume_from_checkpoint(self, path: str | Path) -> None:
        checkpoint = Path(path)
        if not checkpoint.exists():
            print(f"resume checkpoint=missing path={checkpoint}", flush=True)
            return
        try:
            payload = torch.load(checkpoint, map_location=self.device, weights_only=False)
            model_state = payload.get("model", {})
            optimizer_state = payload.get("optimizer", {})
            self.model.load_state_dict(model_state)
            if optimizer_state:
                self.optimizer.load_state_dict(optimizer_state)
            print(f"resume checkpoint=loaded path={checkpoint}", flush=True)
        except Exception as exc:
            print(f"resume checkpoint=skipped path={checkpoint} error={type(exc).__name__}: {exc}", flush=True)

    def _episode_return(self, step_player: int, final_info: dict[str, Any], truncated: bool) -> float:
        if truncated:
            return -1.0
        winner = int(final_info.get("winner", -1))
        if winner == -1:
            return 0.0
        return 1.0 if winner == int(step_player) else -1.0

    def _shape_step_reward(
        self,
        acting_player: int,
        prev_state: dict[str, Any],
        next_state: dict[str, Any],
        final_info: dict[str, Any],
        terminated: bool,
        truncated: bool,
    ) -> float:
        prev_player = prev_state["players"][int(acting_player)]
        prev_opp = prev_state["players"][1 - int(acting_player)]
        next_player = next_state["players"][int(acting_player)]
        next_opp = next_state["players"][1 - int(acting_player)]

        score_delta = (int(next_player.get("score", 0)) - int(prev_player.get("score", 0))) - (
            int(next_opp.get("score", 0)) - int(prev_opp.get("score", 0))
        )
        life_delta = (len(next_player.get("success_lives", [])) - len(prev_player.get("success_lives", []))) - (
            len(next_opp.get("success_lives", [])) - len(prev_opp.get("success_lives", []))
        )
        reward = 0.12 * float(score_delta) + 0.45 * float(life_delta)
        if terminated:
            winner = int(final_info.get("winner", -1))
            if winner == -1:
                reward += 0.0
            else:
                reward += 1.0 if winner == int(acting_player) else -1.0
        elif truncated:
            reward -= 1.0
        return float(reward)

    def _state_strategy(self, state_json: dict[str, Any], current_player: int) -> StateStrategicEvaluation:
        return evaluate_state_strategic_value(
            state_json,
            current_player,
            self.env.card_lookup,
            max_turns=self.config.max_turns,
        )

    def _card_strength(self, card_id: int) -> float:
        if card_id < 0:
            return 0.0
        static = self.env.card_lookup.get(int(card_id), {})
        if not static:
            return 0.0
        primary = float(static.get("primary_value", 0.0))
        hearts = float(static.get("hearts_total", 0.0))
        aux = float(static.get("aux_icons", 0.0))
        groups = float(static.get("group_count", 0.0))
        return 0.35 * (primary / 20.0) + 0.45 * (hearts / 20.0) + 0.15 * (aux / 20.0) + 0.05 * (groups / 12.0)

    def _card_live_fit(self, card_id: int, deficits_by_color: Sequence[float]) -> float:
        return float(live_card_fit_score(card_id, deficits_by_color, self.env.card_lookup))

    def _candidate_focus_card(self, record: dict[str, Any]) -> int:
        for key in (
            "source_hand_card_id",
            "source_stage_card_id",
            "source_live_card_id",
            "target_stage_card_id",
        ):
            card_id = int(record.get(key, -1))
            if card_id >= 0:
                return card_id
        return -1

    def _candidate_action_kind(self, record: dict[str, Any]) -> str:
        family = str(record.get("family", "")).lower()
        params = dict(record.get("params", {}) or {})
        if "discard" in family or any(key in params for key in ("discard_idx", "discard_card_idx", "discard_hand_idx")):
            return "discard"
        if any(key in params for key in ("pick_idx", "choice_idx", "select_idx", "search_idx")):
            return "pick"
        if "pick" in family or "select" in family or "search" in family or "reveal" in family:
            return "pick"
        if "playmember" in family or "setlive" in family:
            return "play"
        if "mulligan" in family:
            return "mulligan"
        if "ability" in family or "trigger" in family or "target" in family:
            return "ability"
        if "result" in family and "live" in family:
            return "resolution"
        if "rps" in family or ("turn" in family and "order" in family):
            return "setup"
        return "other"

    def _heuristic_candidate_score(
        self,
        record: dict[str, Any],
        state_eval: StateStrategicEvaluation | None = None,
    ) -> float:
        family = str(record.get("family", "")).lower()
        turn = max(0, int(record.get("turn", 0)))
        urgency = min(float(turn) / 10.0, 1.0)
        source_card = int(record.get("source_hand_card_id", -1))
        if source_card < 0:
            source_card = int(record.get("source_stage_card_id", -1))
        if source_card < 0:
            source_card = int(record.get("source_live_card_id", -1))
        target_card = int(record.get("target_stage_card_id", -1))
        source_strength = self._card_strength(source_card)
        target_strength = self._card_strength(target_card)
        focus_card = self._candidate_focus_card(record)
        focus_strength = self._card_strength(focus_card)
        deficits: Sequence[float] = tuple(state_eval.best_live_deficit_by_color) if state_eval is not None else ()
        source_fit = self._card_live_fit(source_card, deficits) if source_card >= 0 else 0.0
        target_fit = self._card_live_fit(target_card, deficits) if target_card >= 0 else 0.0
        focus_fit = self._card_live_fit(focus_card, deficits) if focus_card >= 0 else 0.0
        action_kind = self._candidate_action_kind(record)

        if action_kind == "pass":
            score = -1.5 - 0.75 * urgency
        elif action_kind == "mulligan":
            score = -0.55 * source_strength - 0.35 * source_fit + 0.20 * (1.0 - urgency)
        elif action_kind == "discard":
            score = 1.05 * (1.0 - focus_fit) + 0.35 * (1.0 - focus_strength) + 0.20 * (1.0 - source_strength) - 0.08 * target_strength
        elif action_kind == "pick":
            score = 1.00 * focus_fit + 0.35 * focus_strength + 0.15 * target_fit + 0.10 * urgency
        elif action_kind == "play":
            score = 1.10 * source_fit + 0.45 * source_strength + 0.20 * target_fit + 0.15 * target_strength + 0.55 * urgency
        elif action_kind == "resolution":
            score = 0.95 * source_fit + 0.30 * source_strength + 0.20 * target_fit + 0.20 * target_strength + 0.45 * urgency
        elif action_kind == "ability":
            score = 0.40 * source_fit + 0.35 * source_strength + 0.20 * focus_fit + 0.15 * target_fit + 0.25 * urgency
        elif action_kind == "setup":
            score = 0.0
        else:
            score = 0.20 * source_fit + 0.20 * source_strength + 0.10 * target_fit + 0.10 * target_strength

        if state_eval is not None:
            score += 0.30 * float(state_eval.best_live_clearability)
            score += 0.10 * float(state_eval.best_live_color_coverage)

        if not bool(record.get("policy_visible", False)):
            score -= 0.25
        if urgency > 0.6 and ("playmember" in family or "setlive" in family or "result" in family):
            score += 0.25 * urgency
        return float(score)

    def _cpu_search_scores(
        self,
        base_state: Any,
        candidate_actions: Sequence[dict[str, Any]],
        state_eval: StateStrategicEvaluation,
        *,
        search_depth: int = 1,
    ) -> tuple[np.ndarray, np.ndarray]:
        if not candidate_actions:
            return np.zeros((0,), dtype=np.float32), np.zeros((0,), dtype=np.float32)

        try:
            horizon = self.engine.SearchHorizon.TurnEnd()
            suggestions = base_state.search_mcts(
                max(1, int(self.config.cpu_search_sims)),
                0.0,
                "original",
                horizon,
                self.engine.EvalMode.Blind,
                None,
                None,
            )
        except Exception:
            suggestions = []

        suggestion_map: dict[int, tuple[float, int]] = {}
        total_visits = 0
        for action_id, score, visits in suggestions:
            action_int = int(action_id)
            visit_int = max(0, int(visits))
            suggestion_map[action_int] = (float(score), visit_int)
            total_visits += visit_int

        heuristic_scores = np.asarray(
            [self._heuristic_candidate_score(candidate, state_eval) for candidate in candidate_actions],
            dtype=np.float32,
        )
        before_state_json = json.loads(base_state.to_json())
        phase_role = str(state_eval.phase_role)
        if phase_role in {"setup", "mulligan"}:
            exact_weight = 0.03
            fit_weight = 0.05
            heuristic_weight = 0.40
            visit_weight = 0.42
            score_weight = 0.10
        elif phase_role in {"liveset", "prompt"}:
            exact_weight = 0.42
            fit_weight = 0.12
            heuristic_weight = 0.14
            visit_weight = 0.22
            score_weight = 0.10
        else:
            exact_weight = 0.45
            fit_weight = 0.10
            heuristic_weight = 0.14
            visit_weight = 0.18
            score_weight = 0.13
        candidate_scores: list[float] = []
        utility_targets: list[float] = []
        for candidate, heuristic_score in zip(candidate_actions, heuristic_scores, strict=False):
            engine_action = int(candidate.get("engine_action", 0))
            search_score, visits = suggestion_map.get(engine_action, (0.0, 0))
            visit_component = float(visits) / float(max(1, total_visits))
            score_component = 1.0 / (1.0 + float(np.exp(-float(search_score))))
            focus_card = self._candidate_focus_card(candidate)
            fit_component = self._card_live_fit(focus_card, state_eval.best_live_deficit_by_color)
            action_kind = self._candidate_action_kind(candidate)
            exact_component = 0.0
            try:
                next_state = base_state.copy()
                next_state.step(self.env.db, engine_action)
                next_state.auto_step(self.env.db)
                after_state_json = json.loads(next_state.to_json())
                move_eval = evaluate_move_strategic_value(
                    before_state_json,
                    after_state_json,
                    int(before_state_json.get("current_player", 0)),
                    self.env.card_lookup,
                    max_turns=self.config.max_turns,
                    source_card_id=int(candidate.get("source_hand_card_id", -1)),
                    family=str(candidate.get("family", "")),
                    policy_visible=bool(candidate.get("policy_visible", False)),
                )
                after_eval = self._state_strategy(after_state_json, int(before_state_json.get("current_player", 0)))
                delta_clearability = float(move_eval.delta_clearability)
                delta_utility = float(move_eval.delta_utility)
                exact_component = float(
                    np.clip(
                        0.45 * (1.0 / (1.0 + np.exp(-2.5 * float(move_eval.move_score))))
                        + 0.25 * (1.0 / (1.0 + np.exp(-3.0 * delta_clearability)))
                        + 0.20 * (1.0 / (1.0 + np.exp(-2.5 * delta_utility)))
                        + 0.10 * float(after_eval.clearability),
                        0.0,
                        1.0,
                    )
                )
                no_progress = (
                    abs(delta_clearability) < 0.01
                    and abs(delta_utility) < 0.01
                    and abs(float(after_eval.score_margin) - float(state_eval.score_margin)) < 0.01
                    and abs(float(after_eval.stage_hearts) - float(state_eval.stage_hearts)) < 0.01
                )
                if no_progress and action_kind in {"play", "ability"}:
                    exact_component = float(np.clip(exact_component * 0.20, 0.0, 1.0))
                elif no_progress and action_kind == "pass":
                    exact_component = float(np.clip(exact_component - 0.15, 0.0, 1.0))
                if int(search_depth) > 1 and not next_state.is_terminal():
                    exact_component = max(
                        exact_component,
                        self._line_search_value(
                            next_state,
                            depth=int(search_depth) - 1,
                            branch_factor=max(1, int(self.config.cpu_search_branch_factor)),
                        ),
                    )
            except Exception:
                exact_component = 0.0
            candidate_score = float(
                visit_weight * visit_component
                + score_weight * score_component
                + exact_weight * exact_component
                + fit_weight * fit_component
                + heuristic_weight * heuristic_score
            )
            candidate_scores.append(candidate_score)
            utility_targets.append(
                float(
                    np.clip(
                        0.18 * state_eval.clearability
                        + 0.22 * state_eval.best_live_clearability
                        + 0.22 * state_eval.strategic_utility
                        + 0.18 * candidate_score
                        + 0.10 * heuristic_score
                        + fit_weight * fit_component
                        + 0.10 * exact_component
                        + 0.05 * max(0.0, exact_component - 0.50),
                        0.0,
                        1.0,
                    )
                )
            )

        return np.asarray(candidate_scores, dtype=np.float32), np.asarray(utility_targets, dtype=np.float32)

    def _line_search_value(
        self,
        state: Any,
        *,
        depth: int,
        branch_factor: int,
    ) -> float:
        depth = max(0, int(depth))
        branch_factor = max(1, int(branch_factor))
        try:
            if state.is_terminal():
                winner = int(state.get_winner())
                if winner == 0:
                    return 1.0
                if winner == 1:
                    return 0.0
                return 0.5
        except Exception:
            return 0.0

        if depth <= 0:
            try:
                state_json = json.loads(state.to_json())
                state_eval = self._state_strategy(state_json, int(state.current_player))
                return float(state_eval.clearability)
            except Exception:
                return 0.0

        try:
            shadow_env = make_real_game_env(
                RealGameEnvConfig(seed=self.config.seed, max_turns=self.config.max_turns),
                max_turns=self.config.max_turns,
            )
            shadow_env.state = state.copy()
            shadow_env._deck_pair = getattr(self.env, "_deck_pair", None)
            shadow_env._episode_index = 0
            obs, info = shadow_env._state_tensor(), shadow_env._build_info()
            candidate_actions = list(info.get("candidate_actions", []))
            if not candidate_actions:
                return float(self._state_strategy(dict(info.get("state_dict", {}) or {}), int(info.get("current_player", 0))).clearability)
            candidate_features = np.asarray(
                info.get("candidate_action_features", np.zeros((0, ACTION_FEATURE_DIM), dtype=np.float32)),
                dtype=np.float32,
            )
            scores, _, state_eval = self._score_candidate_actions(
                obs,
                info,
                candidate_actions,
                candidate_features,
                use_model=False,
                base_state=shadow_env.state.copy(),
                search_depth=depth,
            )
            if scores.size == 0:
                return float(state_eval.clearability)
            top_count = min(branch_factor, int(scores.size))
            top_indices = np.argsort(scores)[::-1][:top_count]
            return float(np.clip(float(np.max(scores[top_indices])) if top_indices.size else float(np.max(scores)), 0.0, 1.0))
        except Exception:
            return 0.0

    def _score_candidate_actions(
        self,
        obs: np.ndarray,
        info: dict[str, Any],
        candidate_actions: Sequence[dict[str, Any]],
        candidate_features: np.ndarray,
        *,
        use_model: bool = True,
        base_state: Any | None = None,
        search_depth: int | None = None,
    ) -> tuple[np.ndarray, np.ndarray, StateStrategicEvaluation]:
        if not candidate_actions:
            current_player = int(info.get("current_player", 0))
            state_eval = self._state_strategy(dict(info.get("state_dict", {}) or {}), current_player)
            return np.zeros((0,), dtype=np.float32), np.zeros((0,), dtype=np.float32), state_eval

        state_eval = self._state_strategy(dict(info.get("state_dict", {}) or {}), int(info.get("current_player", 0)))
        utility_targets: list[float] = []
        candidate_scores: list[float] = []

        if not use_model:
            search_state = base_state.copy() if base_state is not None else self.env.state.copy()
            return (
                *self._cpu_search_scores(
                    search_state,
                    candidate_actions,
                    state_eval,
                    search_depth=search_depth if search_depth is not None else int(self.config.cpu_search_depth),
                ),
                state_eval,
            )

        policy_scores = np.zeros((len(candidate_actions),), dtype=np.float32)
        heuristic_scores = np.asarray(
            [self._heuristic_candidate_score(candidate, state_eval) for candidate in candidate_actions],
            dtype=np.float32,
        )
        model_move_scores = np.zeros((len(candidate_actions),), dtype=np.float32)
        phase_role = str(state_eval.phase_role)
        phase_bias = {
            "setup": 0.10,
            "mulligan": 0.05,
            "liveset": 0.20,
            "prompt": 0.15,
            "main": 0.25,
            "resolution": 0.18,
        }.get(phase_role, 0.10)

        for index, candidate in enumerate(candidate_actions):
            family = str(candidate.get("family", "")).lower()
            source_card = int(candidate.get("source_hand_card_id", -1))
            if source_card < 0:
                source_card = int(candidate.get("source_stage_card_id", -1))
            if source_card < 0:
                source_card = int(candidate.get("source_live_card_id", -1))
            target_card = int(candidate.get("target_stage_card_id", -1))
            source_strength = self._card_strength(source_card)
            target_strength = self._card_strength(target_card)
            source_cost = 0.12 * source_strength if source_card >= 0 else 0.0
            focus_card = self._candidate_focus_card(candidate)
            focus_strength = self._card_strength(focus_card)
            source_fit = self._card_live_fit(source_card, state_eval.best_live_deficit_by_color) if source_card >= 0 else 0.0
            target_fit = self._card_live_fit(target_card, state_eval.best_live_deficit_by_color) if target_card >= 0 else 0.0
            focus_fit = self._card_live_fit(focus_card, state_eval.best_live_deficit_by_color) if focus_card >= 0 else 0.0
            action_kind = self._candidate_action_kind(candidate)

            if action_kind == "pass":
                move_bias = -0.35 - 0.10 * state_eval.turn_pressure
            elif action_kind == "mulligan":
                move_bias = 0.12 * (1.0 - source_strength) + 0.10 * (1.0 - source_fit) + 0.08 * state_eval.useful_card_density
            elif action_kind == "discard":
                move_bias = 0.34 * (1.0 - focus_fit) + 0.18 * (1.0 - focus_strength) + 0.12 * (1.0 - source_strength) + 0.08 * state_eval.useful_card_density
            elif action_kind == "pick":
                move_bias = 0.22 * focus_fit + 0.18 * focus_strength + 0.12 * target_fit + 0.10 * target_strength + 0.10 * state_eval.clearability + phase_bias
            elif action_kind == "play":
                move_bias = 0.24 * source_fit + 0.18 * source_strength + 0.12 * target_fit + 0.12 * target_strength + 0.22 * state_eval.clearability + phase_bias
            elif action_kind == "resolution":
                move_bias = 0.18 * state_eval.clearability + 0.12 * state_eval.strategic_utility + 0.10 * target_fit + 0.08 * target_strength
            elif action_kind == "ability":
                move_bias = (
                    0.20 * state_eval.strategic_utility
                    + 0.16 * state_eval.clearability
                    + 0.12 * focus_fit
                    + 0.08 * focus_strength
                    + 0.08 * target_fit
                    + 0.07 * target_strength
                )
            elif action_kind == "setup":
                move_bias = 0.0
            else:
                move_bias = 0.10 * source_fit + 0.08 * source_strength + 0.05 * target_fit + 0.05 * target_strength + 0.10 * state_eval.clearability + 0.10 * state_eval.strategic_utility

            if not bool(candidate.get("policy_visible", False)):
                move_bias -= 0.05
            if state_eval.phase_role == "resolution":
                move_bias += 0.05 * state_eval.live_margin
            if state_eval.phase_role == "main":
                move_bias += 0.05 * state_eval.score_margin

            candidate_utility = float(np.clip(
                0.42 * state_eval.clearability
                + 0.20 * state_eval.best_live_clearability
                + 0.28 * state_eval.strategic_utility
                + 0.15 * move_bias
                - source_cost,
                0.0,
                1.0,
            ))
            utility_targets.append(candidate_utility)
            candidate_scores.append(
                0.18 * float(policy_scores[index])
                + 0.18 * float(model_move_scores[index])
                + 0.44 * float(heuristic_scores[index])
                + 0.15 * candidate_utility
            )

        if use_model:
            obs_t = torch.from_numpy(np.asarray(obs, dtype=np.float32)).to(self.device, non_blocking=True).unsqueeze(0)
            state_context = torch.from_numpy(_state_context_from_info(info, self.env.card_lookup, self.config.max_turns)).to(self.device, non_blocking=True).unsqueeze(0)
            cand_t = torch.from_numpy(np.asarray(candidate_features, dtype=np.float32)).to(self.device, non_blocking=True).unsqueeze(0)
            mask_t = torch.ones((1, cand_t.shape[1]), dtype=torch.bool, device=self.device)
            with torch.no_grad():
                logits, _value_pred, _prompt_logits, clearability_pred, utility_pred, move_pred, _tokens = self.model(obs_t, state_context, cand_t, mask_t)
            policy_scores = logits[0].detach().float().cpu().numpy()
            model_move_scores = move_pred[0].detach().float().cpu().numpy()
            if np.isfinite(float(clearability_pred.item())):
                candidate_scores = [score + 0.05 * float(torch.sigmoid(clearability_pred).item()) for score in candidate_scores]
            if np.isfinite(float(utility_pred.item())):
                candidate_scores = [score + 0.05 * float(torch.sigmoid(utility_pred).item()) for score in candidate_scores]
            candidate_scores = [
                0.34 * float(policy_scores[index])
                + 0.33 * float(model_move_scores[index])
                + 0.15 * float(heuristic_scores[index])
                + 0.18 * candidate_utility
                for index, candidate_utility in enumerate(utility_targets)
            ]

        return np.asarray(candidate_scores, dtype=np.float32), np.asarray(utility_targets, dtype=np.float32), state_eval

    def _score_candidate_groups(
        self,
        groups: Sequence[dict[str, Any]],
        *,
        use_model: bool = True,
    ) -> tuple[list[np.ndarray], list[np.ndarray], list[StateStrategicEvaluation]]:
        if not groups:
            return [], [], []

        state_evals = [
            self._state_strategy(dict(group.get("info", {}).get("state_dict", {}) or {}), int(group.get("info", {}).get("current_player", 0)))
            for group in groups
        ]
        utility_targets_per_group: list[np.ndarray] = []
        candidate_scores_per_group: list[np.ndarray] = []

        if use_model:
            policy_scores_batch = [np.zeros((len(group.get("candidate_actions", [])),), dtype=np.float32) for group in groups]
            model_move_scores_batch = [np.zeros((len(group.get("candidate_actions", [])),), dtype=np.float32) for group in groups]
            clearability_bonus = [0.0 for _ in groups]
            utility_bonus = [0.0 for _ in groups]
            obs_batch = np.stack([np.asarray(group["obs"], dtype=np.float32) for group in groups], axis=0)
            state_context_batch = np.stack([
                _state_context_from_info(group["info"], self.env.card_lookup, self.config.max_turns)
                for group in groups
            ], axis=0)
            max_candidates = max(np.asarray(group["candidate_features"], dtype=np.float32).shape[0] for group in groups)
            candidate_dim = np.asarray(groups[0]["candidate_features"], dtype=np.float32).shape[1] if np.asarray(groups[0]["candidate_features"], dtype=np.float32).size else ACTION_FEATURE_DIM
            candidate_batch = np.zeros((len(groups), max_candidates, candidate_dim), dtype=np.float32)
            candidate_mask = np.zeros((len(groups), max_candidates), dtype=np.bool_)
            for row, group in enumerate(groups):
                cand = np.asarray(group["candidate_features"], dtype=np.float32)
                if cand.ndim == 1:
                    cand = cand.reshape(1, -1)
                if cand.size > 0:
                    limit = min(cand.shape[0], max_candidates)
                    candidate_batch[row, :limit, : cand.shape[1]] = cand[:limit, :candidate_dim]
                    candidate_mask[row, :limit] = True
            obs_t = torch.from_numpy(obs_batch).to(self.device, non_blocking=True)
            state_context_t = torch.from_numpy(state_context_batch).to(self.device, non_blocking=True)
            candidate_batch_t = torch.from_numpy(candidate_batch).to(self.device, non_blocking=True)
            candidate_mask_t = torch.from_numpy(candidate_mask).to(self.device, non_blocking=True)
            with torch.no_grad():
                logits, _value_pred, _prompt_logits, clearability_pred, utility_pred, move_pred, _tokens = self.model(
                    obs_t,
                    state_context_t,
                    candidate_batch_t,
                    candidate_mask_t,
                )
            policy_scores_batch = [row.detach().float().cpu().numpy() for row in logits]
            model_move_scores_batch = [row.detach().float().cpu().numpy() for row in move_pred]
            clearability_bonus = [float(torch.sigmoid(v).item()) for v in clearability_pred]
            utility_bonus = [float(torch.sigmoid(v).item()) for v in utility_pred]

        for index, group in enumerate(groups):
            candidate_actions = list(group.get("candidate_actions", []))
            candidate_features = np.asarray(group.get("candidate_features", np.zeros((0, ACTION_FEATURE_DIM), dtype=np.float32)), dtype=np.float32)
            state_eval = state_evals[index]
            if not use_model:
                base_state = group.get("state")
                if base_state is None:
                    raise ValueError("Parallel CPU rollout scoring requires a copied state")
                scores, utility_targets, state_eval = self._score_candidate_actions(
                    np.asarray(group["obs"], dtype=np.float32),
                    group["info"],
                    candidate_actions,
                    candidate_features,
                    use_model=False,
                    base_state=base_state,
                )
                candidate_scores_per_group.append(np.asarray(scores, dtype=np.float32))
                utility_targets_per_group.append(np.asarray(utility_targets, dtype=np.float32))
                continue

            heuristic_scores = np.asarray(
                [self._heuristic_candidate_score(candidate, state_eval) for candidate in candidate_actions],
                dtype=np.float32,
            )
            phase_role = str(state_eval.phase_role)
            phase_bias = {
                "setup": 0.10,
                "mulligan": 0.05,
                "liveset": 0.20,
                "prompt": 0.15,
                "main": 0.25,
                "resolution": 0.18,
            }.get(phase_role, 0.10)
            utility_targets: list[float] = []
            candidate_scores: list[float] = []
            policy_scores = policy_scores_batch[index]
            model_move_scores = model_move_scores_batch[index]
            for cand_index, candidate in enumerate(candidate_actions):
                family = str(candidate.get("family", "")).lower()
                source_card = int(candidate.get("source_hand_card_id", -1))
                if source_card < 0:
                    source_card = int(candidate.get("source_stage_card_id", -1))
                if source_card < 0:
                    source_card = int(candidate.get("source_live_card_id", -1))
                target_card = int(candidate.get("target_stage_card_id", -1))
                source_strength = self._card_strength(source_card)
                target_strength = self._card_strength(target_card)
                source_cost = 0.12 * source_strength if source_card >= 0 else 0.0
                focus_card = self._candidate_focus_card(candidate)
                focus_strength = self._card_strength(focus_card)
                action_kind = self._candidate_action_kind(candidate)

                if action_kind == "pass":
                    move_bias = -0.35 - 0.10 * state_eval.turn_pressure
                elif action_kind == "mulligan":
                    move_bias = 0.12 * (1.0 - source_strength) + 0.08 * state_eval.useful_card_density
                elif action_kind == "discard":
                    move_bias = 0.28 * (1.0 - focus_strength) + 0.12 * (1.0 - source_strength) + 0.08 * state_eval.useful_card_density
                elif action_kind == "pick":
                    move_bias = 0.18 * focus_strength + 0.12 * target_strength + 0.10 * state_eval.clearability + phase_bias
                elif action_kind == "play":
                    move_bias = 0.18 * source_strength + 0.12 * target_strength + 0.20 * state_eval.clearability + phase_bias
                elif action_kind == "resolution":
                    move_bias = 0.16 * state_eval.clearability + 0.10 * state_eval.strategic_utility + 0.08 * target_strength
                elif action_kind == "ability":
                    move_bias = (
                        0.20 * state_eval.strategic_utility
                        + 0.15 * state_eval.clearability
                        + 0.08 * focus_strength
                        + 0.07 * target_strength
                    )
                elif action_kind == "setup":
                    move_bias = 0.0
                else:
                    move_bias = 0.08 * source_strength + 0.04 * target_strength + 0.10 * state_eval.clearability + 0.10 * state_eval.strategic_utility

                if not bool(candidate.get("policy_visible", False)):
                    move_bias -= 0.05
                if state_eval.phase_role == "resolution":
                    move_bias += 0.05 * state_eval.live_margin
                if state_eval.phase_role == "main":
                    move_bias += 0.05 * state_eval.score_margin

                candidate_utility = float(np.clip(
                    0.50 * state_eval.clearability
                    + 0.35 * state_eval.strategic_utility
                    + 0.15 * move_bias
                    - source_cost,
                    0.0,
                    1.0,
                ))
                utility_targets.append(candidate_utility)
                candidate_scores.append(
                    0.34 * float(policy_scores[cand_index]) if cand_index < len(policy_scores) else 0.0
                )
                candidate_scores[-1] += 0.33 * float(model_move_scores[cand_index]) if cand_index < len(model_move_scores) else 0.0
                candidate_scores[-1] += 0.18 * float(heuristic_scores[cand_index]) if cand_index < len(heuristic_scores) else 0.0
                candidate_scores[-1] += 0.15 * candidate_utility

            if use_model and clearability_bonus[index] and candidate_scores:
                candidate_scores = [score + 0.05 * clearability_bonus[index] for score in candidate_scores]
            if use_model and utility_bonus[index] and candidate_scores:
                candidate_scores = [score + 0.05 * utility_bonus[index] for score in candidate_scores]

            utility_targets_per_group.append(np.asarray(utility_targets, dtype=np.float32))
            candidate_scores_per_group.append(np.asarray(candidate_scores, dtype=np.float32))

        return candidate_scores_per_group, utility_targets_per_group, state_evals

    def _collect_episode_core(
        self,
        env: RealGameEnv,
        episode_index: int,
        rng: random.Random,
    ) -> tuple[list[TrajectoryStep], dict[str, Any]]:
        obs, info = env.reset(seed=self.config.seed + episode_index)
        episode: list[TrajectoryStep] = []
        done = False
        step_index = 0
        epsilon = _linear_schedule(self.config.epsilon_start, self.config.epsilon_end, episode_index, max(self.config.episodes - 1, 1))
        temperature = _linear_schedule(self.config.temperature_start, self.config.temperature_end, episode_index, max(self.config.episodes - 1, 1))

        while not done:
            prev_state = info.get("state_dict", {})
            state_eval = self._state_strategy(dict(prev_state or {}), int(info.get("current_player", 0)))
            state_context = _state_context_from_info(info, env.card_lookup, self.config.max_turns)
            candidate_features = np.asarray(info.get("candidate_action_features", np.zeros((0, ACTION_FEATURE_DIM), dtype=np.float32)), dtype=np.float32)
            candidate_actions = list(info.get("candidate_actions", []))
            if len(candidate_actions) == 0:
                action = 0
                action_index = 0
                policy_target = np.zeros((0,), dtype=np.float32)
                candidate_utility_targets = np.zeros((0,), dtype=np.float32)
            else:
                scores, candidate_utility_targets, state_eval = self._score_candidate_actions(
                    obs,
                    info,
                    candidate_actions,
                    candidate_features,
                    use_model=bool(self.config.self_play_use_model),
                    base_state=env.state.copy() if not self.config.self_play_use_model else None,
                )
                policy_target = _softmax_distribution(scores, temperature)
                if rng.random() < float(epsilon):
                    action_index = int(rng.randrange(len(candidate_actions)))
                else:
                    action_index = int(np.argmax(np.asarray(scores, dtype=np.float32)))
                action = int(candidate_actions[action_index]["engine_action"])

            acting_player = int(info.get("current_player", 0))
            obs, reward, terminated, truncated, info = env.step(action)
            next_state = dict(info.get("state_dict", {}))
            shaped_reward = self._shape_step_reward(
                acting_player,
                prev_state,
                next_state,
                info,
                bool(terminated),
                bool(truncated),
            )
            episode.append(
                    TrajectoryStep(
                        obs=np.asarray(obs, dtype=np.float32),
                        state_context=np.asarray(state_context, dtype=np.float32),
                        candidate_features=candidate_features,
                        policy_target=np.asarray(policy_target, dtype=np.float32),
                    candidate_utility_targets=np.asarray(candidate_utility_targets, dtype=np.float32),
                    action_index=action_index,
                    player=acting_player,
                    clearability_target=float(state_eval.clearability),
                    utility_target=float(state_eval.strategic_utility),
                    reward=shaped_reward,
                )
            )
            done = bool(terminated or truncated)
            step_index += 1
            if step_index > max(self.config.max_turns * 128, 256):
                break

        try:
            env.close()
        except Exception:
            pass
        return episode, info

    def collect_parallel_episodes(self, batch_count: int, episode_start_index: int) -> tuple[list[list[TrajectoryStep]], list[dict[str, Any]]]:
        episodes: list[list[TrajectoryStep]] = [[] for _ in range(batch_count)]
        finals: list[dict[str, Any]] = [{} for _ in range(batch_count)]
        if batch_count <= 1:
            episode, final_info = self.collect_episode(episode_start_index)
            return [episode], [final_info]

        if bool(self.config.self_play_use_model):
            for offset in range(batch_count):
                episode, final_info = self.collect_episode(episode_start_index + offset)
                episodes[offset] = episode
                finals[offset] = final_info
            return episodes, finals

        with ThreadPoolExecutor(max_workers=batch_count) as executor:
            futures = []
            for offset in range(batch_count):
                episode_index = episode_start_index + offset
                env = make_real_game_env(
                    RealGameEnvConfig(seed=self.config.seed + episode_index, max_turns=self.config.max_turns),
                    max_turns=self.config.max_turns,
                )
                futures.append(
                    executor.submit(
                        self._collect_episode_core,
                        env,
                        episode_index,
                        random.Random(self.config.seed + episode_index),
                    )
                )
            for offset, future in enumerate(futures):
                episode, final_info = future.result()
                episodes[offset] = episode
                finals[offset] = final_info

        return episodes, finals

    def collect_episode(self, episode_index: int) -> tuple[list[TrajectoryStep], dict[str, Any]]:
        env = make_real_game_env(
            RealGameEnvConfig(seed=self.config.seed + episode_index, max_turns=self.config.max_turns),
            max_turns=self.config.max_turns,
        )
        return self._collect_episode_core(env, episode_index, random.Random(self.config.seed + episode_index))

    def _discount_returns(self, rewards: Sequence[float], gamma: float = 0.98) -> list[float]:
        running = 0.0
        returns = [0.0] * len(rewards)
        for idx in range(len(rewards) - 1, -1, -1):
            running = float(rewards[idx]) + gamma * running
            returns[idx] = running
        return returns

    def _train_step(self, sample: DiskReplaySample) -> dict[str, float]:
        if int(sample.obs.shape[0]) <= 0:
            return {"loss": 0.0, "policy_loss": 0.0, "value_loss": 0.0, "entropy": 0.0}

        obs = torch.from_numpy(np.asarray(sample.obs, dtype=np.float32)).to(self.device, non_blocking=True)
        state_context = torch.from_numpy(np.asarray(sample.state_context, dtype=np.float32)).to(self.device, non_blocking=True)
        candidate_batch = torch.from_numpy(np.asarray(sample.candidate_features, dtype=np.float32)).to(self.device, non_blocking=True)
        candidate_mask = torch.from_numpy(np.asarray(sample.candidate_mask, dtype=np.bool_)).to(self.device, non_blocking=True)
        value_target = torch.from_numpy(np.asarray(sample.value_target, dtype=np.float32)).to(self.device, non_blocking=True)
        clearability_target = torch.from_numpy(np.asarray(sample.clearability_target, dtype=np.float32)).to(self.device, non_blocking=True)
        utility_target = torch.from_numpy(np.asarray(sample.utility_target, dtype=np.float32)).to(self.device, non_blocking=True)
        target_policy = torch.from_numpy(np.asarray(sample.policy_target, dtype=np.float32)).to(self.device, non_blocking=True)
        target_move_utility = torch.from_numpy(np.asarray(sample.move_utility_target, dtype=np.float32)).to(self.device, non_blocking=True)
        action_index = torch.from_numpy(np.asarray(sample.action_index, dtype=np.int64)).to(self.device, non_blocking=True)

        if obs.ndim == 1:
            obs = obs.unsqueeze(0)
            state_context = state_context.unsqueeze(0)
            candidate_batch = candidate_batch.unsqueeze(0)
            candidate_mask = candidate_mask.unsqueeze(0)
            value_target = value_target.unsqueeze(0)
            clearability_target = clearability_target.unsqueeze(0)
            utility_target = utility_target.unsqueeze(0)
            target_policy = target_policy.unsqueeze(0)
            target_move_utility = target_move_utility.unsqueeze(0)
            action_index = action_index.unsqueeze(0)

        if candidate_batch.shape[0] != obs.shape[0]:
            raise ValueError("Replay batch shapes are inconsistent")

        empty_rows = ~candidate_mask.any(dim=-1)
        if bool(empty_rows.any()):
            candidate_batch = candidate_batch.clone()
            candidate_mask = candidate_mask.clone()
            target_policy = target_policy.clone()
            target_move_utility = target_move_utility.clone()
            action_index = action_index.clone()
            candidate_mask[empty_rows, 0] = True
            target_policy[empty_rows] = 0
            target_policy[empty_rows, 0] = 1.0
            action_index[empty_rows] = 0

        action_index = torch.clamp(action_index, min=0, max=max(candidate_batch.shape[1] - 1, 0))
        prompt_target = torch.clamp(torch.round(state_context[:, 22] * 7.0), 0, 7).long()
        family_target = torch.zeros((obs.shape[0],), dtype=torch.long, device=self.device)
        for row in range(int(obs.shape[0])):
            idx = int(action_index[row].item())
            if idx < candidate_batch.shape[1]:
                family_target[row] = int(torch.argmax(candidate_batch[row, idx, :9]).item())

        target_policy = target_policy / target_policy.sum(dim=-1, keepdim=True).clamp_min(1e-6)

        with torch.autocast(device_type=self.device.type, dtype=torch.float16, enabled=self.device.type == "cuda"):
            logits, value_pred, prompt_logits, clearability_pred, utility_pred, move_pred, mixed_tokens = self.model(obs, state_context, candidate_batch, candidate_mask)
            log_probs = F.log_softmax(logits, dim=-1)
            probs = torch.softmax(logits, dim=-1)
            policy_loss = -(target_policy * log_probs).sum(dim=-1)
            policy_weight = torch.clamp(0.8 + 0.6 * clearability_target + 0.4 * utility_target, 0.5, 1.8)
            policy_loss = (policy_loss * policy_weight).mean()
            value_loss = F.smooth_l1_loss(value_pred, value_target)
            clearability_loss = F.smooth_l1_loss(torch.sigmoid(clearability_pred), clearability_target)
            utility_loss = F.smooth_l1_loss(torch.sigmoid(utility_pred), utility_target)
            prompt_loss = F.cross_entropy(prompt_logits, prompt_target)
            chosen_candidate_tokens = mixed_tokens[torch.arange(obs.shape[0], device=self.device), 1 + action_index]
            family_logits = self.model.family_head(chosen_candidate_tokens)
            family_loss = F.cross_entropy(family_logits, family_target)
            move_mask = candidate_mask
            move_loss = F.smooth_l1_loss(
                move_pred[move_mask],
                target_move_utility[move_mask],
            ) if bool(move_mask.any()) else torch.tensor(0.0, device=self.device)
            entropy = -(probs * log_probs).sum(dim=-1).mean()
            aux_loss = 0.15 * prompt_loss + 0.10 * family_loss + 0.20 * clearability_loss + 0.20 * utility_loss + 0.20 * move_loss
            loss = policy_loss + self.config.value_coef * value_loss + aux_loss - self.config.entropy_coef * entropy

        self.optimizer.zero_grad(set_to_none=True)
        if self.device.type == "cuda":
            self.scaler.scale(loss).backward()
            self.scaler.unscale_(self.optimizer)
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()

        return {
            "loss": float(loss.item()),
            "policy_loss": float(policy_loss.item()),
            "value_loss": float(value_loss.item()),
            "clearability_loss": float(clearability_loss.item()),
            "utility_loss": float(utility_loss.item()),
            "move_loss": float(move_loss.item()),
            "prompt_loss": float(prompt_loss.item()),
            "family_loss": float(family_loss.item()),
            "entropy": float(entropy.item()),
        }

    def train(self) -> dict[str, float]:
        self.model.train()
        history: list[dict[str, float]] = []
        last_save_time = time.monotonic()
        start_time = last_save_time
        last_log_time = start_time
        steps_since_log = 0
        games_since_log = 0
        total_steps = 0
        total_games = 0
        save_interval = max(1, int(self.config.save_interval_seconds))
        log_interval = max(1, int(self.config.log_every_episodes))
        print(
            f"training_start episodes={self.config.episodes} batch_size={self.config.batch_size} "
            f"hidden_dim={self.config.hidden_dim} replay_capacity={self.config.replay_buffer_capacity} "
            f"self_play_use_model={int(self.config.self_play_use_model)} "
            f"parallel_self_play_games={self.config.parallel_self_play_games} "
            f"cpu_search_sims={self.config.cpu_search_sims}",
            flush=True,
        )

        episode_index = 0
        parallel_games = max(1, int(self.config.parallel_self_play_games))
        while episode_index < self.config.episodes:
            batch_count = min(parallel_games, self.config.episodes - episode_index)
            collect_start = time.monotonic()
            if batch_count > 1:
                batch_episodes, batch_finals = self.collect_parallel_episodes(batch_count, episode_index)
                episode_pairs = list(zip(batch_episodes, batch_finals, strict=False))
            else:
                episode, final_info = self.collect_episode(episode_index)
                episode_pairs = [(episode, final_info)]
            collect_elapsed = max(time.monotonic() - collect_start, 1e-6)
            collect_steps = sum(len(episode) for episode, _final in episode_pairs)
            collect_games = len(episode_pairs)

            for local_offset, (episode, final_info) in enumerate(episode_pairs):
                current_episode = episode_index + local_offset
                truncated = bool(final_info.get("turn_limit_reached", False))
                episode_targets = [self._episode_return(step.player, final_info, truncated) for step in episode]
                total_steps += len(episode)
                total_games += 1
                steps_since_log += len(episode)
                games_since_log += 1
                for step, target in zip(episode, episode_targets, strict=False):
                    candidate_mask = np.ones((step.candidate_features.shape[0],), dtype=np.uint8)
                    self.replay.add(
                        obs=step.obs,
                        state_context=step.state_context,
                        candidate_features=step.candidate_features,
                        candidate_mask=candidate_mask,
                        policy_target=step.policy_target,
                        move_utility_target=step.candidate_utility_targets,
                        action_index=step.action_index,
                        value_target=float(target),
                        clearability_target=float(step.clearability_target),
                        utility_target=float(step.utility_target),
                    )

                batch_stats = {"loss": 0.0, "policy_loss": 0.0, "value_loss": 0.0, "entropy": 0.0}
                for _ in range(max(1, self.config.updates_per_episode)):
                    if len(self.replay) <= 0:
                        break
                    batch = self.replay.sample(self.config.batch_size)
                    if batch is None:
                        break
                    batch_stats = self._train_step(batch)
                history.append(batch_stats)

                if (current_episode + 1) % 8 == 0 or current_episode == 0:
                    avg_loss = sum(item["loss"] for item in history[-8:]) / min(len(history), 8)
                    avg_policy = sum(item["policy_loss"] for item in history[-8:]) / min(len(history), 8)
                    avg_value = sum(item["value_loss"] for item in history[-8:]) / min(len(history), 8)
                    avg_entropy = sum(item["entropy"] for item in history[-8:]) / min(len(history), 8)
                    print(
                        f"episode={current_episode + 1:04d} replay={len(self.replay):04d} "
                        f"loss={avg_loss:.4f} policy={avg_policy:.4f} value={avg_value:.4f} entropy={avg_entropy:.4f}",
                        flush=True,
                    )

                if (current_episode + 1) % log_interval == 0:
                    turn = int(final_info.get("turn", 0))
                    winner = int(final_info.get("winner", -1))
                    turn_limit = bool(final_info.get("turn_limit_reached", False))
                    now = time.monotonic()
                    elapsed = max(now - start_time, 1e-6)
                    interval = max(now - last_log_time, 1e-6)
                    steps_per_sec = float(steps_since_log) / interval
                    games_per_sec = float(games_since_log) / interval
                    overall_steps_per_sec = float(total_steps) / elapsed
                    overall_games_per_sec = float(total_games) / elapsed
                    collect_steps_per_sec = float(collect_steps) / collect_elapsed
                    collect_games_per_sec = float(collect_games) / collect_elapsed
                    print(
                        f"progress episode={current_episode + 1:04d} steps={len(episode):03d} turn={turn:02d} "
                        f"winner={winner} turn_limit={int(turn_limit)} replay={len(self.replay):04d} "
                        f"loss={batch_stats['loss']:.4f} policy={batch_stats['policy_loss']:.4f} "
                        f"value={batch_stats['value_loss']:.4f} clear={batch_stats['clearability_loss']:.4f} "
                        f"utility={batch_stats['utility_loss']:.4f} move={batch_stats['move_loss']:.4f} "
                        f"steps_per_sec={steps_per_sec:.1f} games_per_sec={games_per_sec:.2f} "
                        f"overall_steps_per_sec={overall_steps_per_sec:.1f} overall_games_per_sec={overall_games_per_sec:.2f} "
                        f"collect_steps_per_sec={collect_steps_per_sec:.1f} collect_games_per_sec={collect_games_per_sec:.2f}",
                        flush=True,
                    )
                    last_log_time = now
                    steps_since_log = 0
                    games_since_log = 0

                now = time.monotonic()
                if now - last_save_time >= float(save_interval):
                    self.replay.flush()
                    self.save(self.config.checkpoint_path)
                    last_save_time = now
                    print(f"autosaved checkpoint={self.config.checkpoint_path} episode={current_episode + 1:04d}")

            episode_index += batch_count

        self.replay.flush()
        return self.evaluate()

    def act(self, obs: np.ndarray, info: dict[str, Any], greedy: bool = True, *, use_model: bool = True) -> int:
        candidate_features = np.asarray(info.get("candidate_action_features", np.zeros((0, ACTION_FEATURE_DIM), dtype=np.float32)), dtype=np.float32)
        candidate_actions = list(info.get("candidate_actions", []))
        if len(candidate_actions) == 0:
            return 0
        if greedy and len(candidate_actions) > 1:
            scores, _move_targets, _state_eval = self._score_candidate_actions(
                obs,
                info,
                candidate_actions,
                candidate_features,
                use_model=use_model,
            )
            chosen_index = int(np.argmax(np.asarray(scores, dtype=np.float32)))
        elif greedy:
            scores, _move_targets, _state_eval = self._score_candidate_actions(
                obs,
                info,
                candidate_actions,
                candidate_features,
                use_model=use_model,
            )
            chosen_index = int(np.argmax(np.asarray(scores, dtype=np.float32)))
        else:
            obs_t = torch.from_numpy(np.asarray(obs, dtype=np.float32)).to(self.device, non_blocking=True).unsqueeze(0)
            state_context = torch.from_numpy(_state_context_from_info(info, self.env.card_lookup, self.config.max_turns)).to(self.device, non_blocking=True).unsqueeze(0)
            cand_t = torch.from_numpy(candidate_features).to(self.device, non_blocking=True).unsqueeze(0)
            mask_t = torch.ones((1, cand_t.shape[1]), dtype=torch.bool, device=self.device)
            with torch.no_grad():
                logits, _value, _prompt_logits, _clear, _utility, _move, _tokens = self.model(obs_t, state_context, cand_t, mask_t)
            probs = torch.softmax(logits[0], dim=-1)
            chosen_index = int(torch.multinomial(probs, 1).item())
        return int(candidate_actions[chosen_index]["engine_action"])

    def evaluate(self) -> dict[str, float]:
        previous_mode = self.model.training
        self.model.eval()
        controlled_wins = 0
        random_games = max(1, int(self.config.eval_games))
        total_turns = 0
        turn_limit_hits = 0

        for game_idx in range(random_games):
            controlled_player = game_idx % 2
            obs, info = self.env.reset(seed=self.config.seed + 10_000 + game_idx)
            done = False
            turn_counter = 0
            while not done:
                current_player = int(info.get("current_player", 0))
                if current_player == controlled_player:
                    action = self.act(obs, info, greedy=True, use_model=True)
                else:
                    raw_actions = list(info.get("raw_legal_action_ids", []))
                    policy_actions = list(info.get("legal_policy_ids", []))
                    legal = policy_actions if policy_actions else raw_actions
                    action = int(self.rng.choice(legal)) if legal else 0
                obs, reward, terminated, truncated, info = self.env.step(action)
                done = bool(terminated or truncated)
                turn_counter += 1
                if turn_counter > max(self.config.max_turns * 128, 256):
                    break

            winner = int(info.get("winner", -1))
            if winner == controlled_player:
                controlled_wins += 1
            total_turns += int(info.get("turn", 0))
            turn_limit_hits += 1 if bool(info.get("turn_limit_reached", False)) else 0

        self.model.train(previous_mode)
        return {
            "eval_games": float(random_games),
            "win_rate_vs_random": float(controlled_wins) / float(random_games),
            "avg_turns": float(total_turns) / float(random_games),
            "turn_limit_rate": float(turn_limit_hits) / float(random_games),
        }

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.replay.flush()
        except Exception:
            pass
        torch.save(
            {
                "model": self.model.state_dict(),
                "optimizer": self.optimizer.state_dict(),
                "config": self.config.__dict__,
            },
            target,
        )


def run_training(config: RealGameTrainerConfig) -> dict[str, float]:
    trainer = RealGameTrainer(config)
    before = trainer.evaluate()
    print(
        f"baseline win_rate_vs_random={before['win_rate_vs_random']:.3f} "
        f"avg_turns={before['avg_turns']:.2f} "
        f"turn_limit_rate={before['turn_limit_rate']:.3f}"
    )
    after = trainer.train()
    print(
        f"trained win_rate_vs_random={after['win_rate_vs_random']:.3f} "
        f"avg_turns={after['avg_turns']:.2f} "
        f"turn_limit_rate={after['turn_limit_rate']:.3f}"
    )
    trainer.save(config.checkpoint_path)
    return after


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Train a real-game self-play agent")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--episodes", type=int, default=64)
    parser.add_argument("--eval-games", type=int, default=16)
    parser.add_argument("--updates-per-episode", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--entropy-coef", type=float, default=0.01)
    parser.add_argument("--value-coef", type=float, default=0.5)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--hidden-dim", type=int, default=1024)
    parser.add_argument("--log-every-episodes", type=int, default=1)
    parser.add_argument("--self-play-use-model", action="store_true")
    parser.add_argument("--parallel-self-play-games", type=int, default=1)
    parser.add_argument("--cpu-search-sims", type=int, default=16)
    parser.add_argument("--replay-buffer-dir", type=str, default="replay/real_game_agent")
    parser.add_argument("--replay-buffer-capacity", type=int, default=4096)
    parser.add_argument("--replay-buffer-max-candidates", type=int, default=128)
    parser.add_argument("--replay-size", type=int, default=None, help="Backward-compatible alias for replay-buffer-capacity")
    parser.add_argument("--save-interval-seconds", type=int, default=300)
    parser.add_argument("--checkpoint-path", type=str, default="checkpoints/real_game_agent.pt")
    args = parser.parse_args(argv)

    config = RealGameTrainerConfig(
        seed=args.seed,
        device=args.device,
        episodes=args.episodes,
        eval_games=args.eval_games,
        updates_per_episode=args.updates_per_episode,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        entropy_coef=args.entropy_coef,
        value_coef=args.value_coef,
        hidden_dim=args.hidden_dim,
        log_every_episodes=args.log_every_episodes,
        self_play_use_model=args.self_play_use_model,
        parallel_self_play_games=args.parallel_self_play_games,
        cpu_search_sims=args.cpu_search_sims,
        replay_size=args.replay_size,
        replay_buffer_capacity=args.replay_buffer_capacity,
        replay_buffer_dir=args.replay_buffer_dir,
        replay_buffer_max_candidates=args.replay_buffer_max_candidates,
        save_interval_seconds=args.save_interval_seconds,
        checkpoint_path=args.checkpoint_path,
    )
    run_training(config)


if __name__ == "__main__":
    main()
