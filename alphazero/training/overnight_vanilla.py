from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib
import json
import logging
import os
import random
import shutil
import signal
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn, optim

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _load_engine_module():
    tmp_engine_target = ROOT_DIR / ".tmp_engine" / "engine_rust.pyd"
    workspace_venv_engine = ROOT_DIR / ".venv" / "Lib" / "site-packages" / "engine_rust" / "engine_rust.pyd"
    sync_sources = (
        workspace_venv_engine,
        ROOT_DIR / "engine_rust_src" / "target" / "release" / "engine_rust_ext.pyd",
        ROOT_DIR / "engine_rust_src" / "target" / "debug" / "engine_rust_ext.pyd",
        ROOT_DIR / "engine_rust_src" / "target" / "release" / "engine_rust_test.pyd",
        ROOT_DIR / "engine_rust_src" / "target" / "debug" / "engine_rust_test.pyd",
        ROOT_DIR / "alphazero" / "training" / "engine_rust.pyd",
        ROOT_DIR / "engine_rust.pyd",
    )
    for source in sync_sources:
        if not source.exists():
            continue
        if not tmp_engine_target.exists() or source.stat().st_mtime > tmp_engine_target.stat().st_mtime:
            tmp_engine_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, tmp_engine_target)
            break

    explicit_candidates = (
        workspace_venv_engine,
        tmp_engine_target,
        ROOT_DIR / "alphazero" / "training" / "engine_rust.pyd",
        ROOT_DIR / "engine_rust.pyd",
    )
    best_module = None
    best_score = -1
    local_shadow_dirs = {
        str((ROOT_DIR / ".tmp_engine").resolve()),
        str(ROOT_DIR.resolve()),
        str((Path(__file__).resolve().parent).resolve()),
    }

    def _module_score(module) -> int:
        return sum(
            int(hasattr(module, attr))
            for attr in (
                "PyCardDatabase",
                "PyGameState",
                "PyAlphaZeroEvaluator",
                "AlphaZeroTensorType",
            )
        )

    for candidate in explicit_candidates:
        if not candidate.exists():
            continue
        candidate_dir = str(candidate.parent)
        added_to_path = False
        if candidate_dir not in sys.path:
            sys.path.insert(0, candidate_dir)
            added_to_path = True
        sys.modules.pop("engine_rust", None)
        try:
            module = importlib.import_module("engine_rust")
        except ImportError:
            if added_to_path:
                sys.path.remove(candidate_dir)
            continue
        score = _module_score(module)
        if score > best_score and hasattr(module, "PyCardDatabase"):
            best_module = module
            best_score = score
        if added_to_path:
            sys.path.remove(candidate_dir)

    for module_name in ("engine_rust", "alphazero.training.engine_rust"):
        original_sys_path = sys.path[:]
        sys.path = [
            entry
            for entry in sys.path
            if str(Path(entry or ".").resolve()) not in local_shadow_dirs
        ]
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            sys.path = original_sys_path
            continue
        finally:
            sys.path = original_sys_path
        score = _module_score(module)
        if score > best_score and hasattr(module, "PyCardDatabase"):
            best_module = module
            best_score = score
    if best_module is not None:
        return best_module
    raise ImportError("No PyO3 engine_rust module with PyCardDatabase was found")


engine_rust = _load_engine_module()

from alphazero.training.disk_buffer import PersistentBuffer
from alphazero.training.overnight_reward import (
    CompetitiveGameRewardBreakdown,
    SeedCertificationSummary,
    competitive_fast_win_reward,
    perspective_fast_win_value,
    seed_certified,
    summarize_seed_certification,
)
from alphazero.training.vanilla_action_codec import (
    ACTION_BASE_PASS,
    ACTION_SPACE,
    build_legal_policy_context,
    dense_to_sparse,
    engine_action_to_policy_id,
    sparse_policy_from_engine_visits,
)
from alphazero.vanilla_net import (
    VANILLA_CARD_FEATURES,
    VANILLA_GLOBAL_FEATURES,
    VANILLA_INPUT_DIM,
    VANILLA_TOTAL_CARDS,
    HighFidelityAlphaNet,
    VanillaTransformerConfig,
)
from engine.game.deck_utils import UnifiedDeckParser

logger = logging.getLogger("overnight_vanilla")

OBSERVATION_MODE_RAW = "raw"
OBSERVATION_MODE_HINT = "human_hint"
OBSERVATION_MODE_FULL = "full"

PHASE_RPS = -3
PHASE_TURN_ORDER = -2

GLOBAL_PORTFOLIO_START = 10
GLOBAL_PORTFOLIO_END = 18
GLOBAL_ACTIVE_LIVE_EV = 18
GLOBAL_CLEARABLE_NOW = 19
CARD_BLOCK_START = VANILLA_GLOBAL_FEATURES
CARD_BLOCK = VANILLA_CARD_FEATURES
CARD_INDIVIDUAL_PROB_OFFSET = 10
CARD_PARTICIPATION_OFFSET = 11

VALUE_OUTCOME_WEIGHT = 0.45
VALUE_LIVE_MARGIN_WEIGHT = 0.35
VALUE_SCORE_MARGIN_WEIGHT = 0.14
VALUE_SPEED_WEIGHT = 0.15
VALUE_IMMEDIATE_LIVE_BONUS = 0.45
VALUE_IMMEDIATE_LIVE_TURN_SCALE = 0.75
VALUE_IMMEDIATE_SCORE_BONUS = 0.14
VALUE_IMMEDIATE_SCORE_TURN_SCALE = 0.9
VALUE_CONTESTED_PASS_PENALTY = 0.12
VALUE_SETUP_PROGRESS_WEIGHT = 0.18
VALUE_COVERAGE_GAIN_WEIGHT = 0.14
VALUE_LIVESET_PROGRESS_WEIGHT = 0.06
VALUE_BATON_PROGRESS_WEIGHT = 0.04

POLICY_IMMEDIATE_LIVE_BOOST = 0.95
POLICY_TURN_URGENCY_SCALE = 0.75
POLICY_IMMEDIATE_SCORE_BOOST = 0.24
POLICY_TERMINAL_WIN_BOOST = 1.0
POLICY_CONTESTED_PASS_DISCOUNT = 0.45
POLICY_SETUP_PROGRESS_BOOST = 0.35
POLICY_COVERAGE_GAIN_BOOST = 0.25
POLICY_LIVESET_PROGRESS_BOOST = 0.12
POLICY_BATON_PROGRESS_BOOST = 0.1
POLICY_SCORE_URGENCY_SCALE = 0.75


@dataclass
class OvernightConfig:
    checkpoint_dir: str = "checkpoints/vanilla_overnight"
    best_checkpoint_name: str = "best.pt"
    buffer_dir: str = "buffers/vanilla_overnight"
    log_csv: str = "checkpoints/vanilla_overnight/training_log.csv"
    benchmark_log_csv: str = "checkpoints/vanilla_overnight/benchmark_log.csv"
    proof_log_csv: str = "checkpoints/vanilla_overnight/single_seed_proof.csv"
    proof_output_json: str = "checkpoints/vanilla_overnight/single_seed_proof.json"
    deck_source: str = "ai/decks/muse_cup.txt"
    db_path: str = "data/cards_vanilla.json"
    model_preset: str = "small"
    training_target_mode: str = "search"
    observation_mode: str = OBSERVATION_MODE_HINT
    selfplay_action_source: str = "search_sample"
    num_iterations: int = 200
    games_per_iteration: int = 32
    training_steps_per_iteration: int = 16
    batch_size: int = 1024
    learning_rate: float = 3e-4
    weight_decay: float = 1e-4
    gradient_clip: float = 1.0
    entropy_coef: float = 0.002
    value_coef: float = 0.5
    buffer_size: int = 4_500_000
    min_buffer_items: int = 4096
    search_sims: int = 12
    neural_mcts_batch_size: int = 16
    actor_temperature: float = 0.8
    actor_epsilon: float = 0.12
    teacher_action_prob: float = 1.0
    min_teacher_action_prob: float = 1.0
    teacher_action_warmup_iters: int = 0
    teacher_action_decay_iters: int = 0
    value_dim: int = 1
    max_turns: int = 10
    seed: int = 1337
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    reset_training_state: bool = False
    eval_games: int = 12
    benchmark_games: int = 24
    benchmark_model_search_sims: int = 0
    benchmark_search_sims: int = 24
    benchmark_every: int = 30
    benchmark_seed_base: int = 200_000
    turnseq_benchmark_games: int = 8
    reference_benchmark_games: int = 12
    target_replay_ratio: float = 8.0
    reference_promote_threshold: float = 0.55
    reference_rollback_threshold: float = 0.40
    rollback_on_reference_regression: bool = True
    deck_rotation_mode: str = "per_iteration"
    proof_games: int = 8
    proof_train_steps: int = 160
    proof_eval_games: int = 1
    checkpoint_every: int = 1
    selfplay_seed_mode: str = "random"
    hard_seed_file: str = "checkpoints/vanilla_overnight/hard_seeds.json"
    hard_seed_ratio: float = 0.5
    hard_seed_scan_games: int = 128
    hard_seed_min_turns: int = 9
    single_seed_plateau_window: int = 4
    single_seed_plateau_delta: float = 0.015
    single_seed_min_iters: int = 4
    single_seed_max_iters: int = 12
    curriculum_eval_games: int = 2
    single_seed_target_reward: float = 1.75
    single_seed_target_decisive_rate: float = 1.0
    single_seed_target_fast_win_rate: float = 0.9
    single_seed_target_avg_turns: float = 6.0
    single_seed_fast_turn_threshold: int = 6
    skip_draw_records: bool = False


SelfPlayConfig = OvernightConfig
VanillaPolicyModel = HighFidelityAlphaNet


@dataclass
class PositionRecord:
    obs: np.ndarray
    policy: np.ndarray
    legal_policy_ids: np.ndarray
    value_target: float


@dataclass
class SelfPlayGameResult:
    records: list[PositionRecord]
    turns: int
    winner: int
    decisions: int
    model_eval_actions: int
    contested_pass_actions: int
    teacher_forced_actions: int
    chosen_teacher_match_actions: int
    model_teacher_match_actions: int
    elapsed_sec: float
    model_infer_sec: float
    teacher_search_sec: float
    env_step_sec: float
    p0_score: int
    p1_score: int
    p0_lives: int
    p1_lives: int


def _configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def _configure_torch_runtime() -> None:
    try:
        torch.set_float32_matmul_precision("high")
    except Exception:
        pass
    if torch.cuda.is_available():
        try:
            torch.backends.cuda.matmul.allow_tf32 = True
        except Exception:
            pass
        try:
            torch.backends.cudnn.allow_tf32 = True
        except Exception:
            pass
        try:
            torch.backends.cudnn.benchmark = True
        except Exception:
            pass


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_vanilla_database_json(db_path: str | Path) -> tuple[dict, str]:
    resolved = Path(db_path)
    if not resolved.is_absolute():
        resolved = ROOT_DIR / resolved
    full_db = json.loads(resolved.read_text(encoding="utf-8"))
    return full_db, json.dumps(full_db)


def _resolve_deck_codes(parser: UnifiedDeckParser, extracted: dict[str, object]) -> dict[str, object]:
    members: list[int] = []
    lives: list[int] = []
    energy: list[int] = []

    for code in extracted.get("main", []):
        resolved = parser.resolve_card(str(code))
        card_id = resolved.get("card_id")
        if card_id is None:
            continue
        if resolved.get("type") == "Member":
            members.append(int(card_id))
        elif resolved.get("type") == "Live":
            lives.append(int(card_id))

    for code in extracted.get("energy", []):
        resolved = parser.resolve_card(str(code))
        card_id = resolved.get("card_id")
        if card_id is not None:
            energy.append(int(card_id))

    initial_deck = (members[:48] + lives[:12])[:60]
    if len(initial_deck) != 60:
        raise ValueError(f"Expected a 60-card initial deck, got {len(initial_deck)}")
    if not energy:
        raise ValueError("Deck has no energy cards")

    return {
        "name": extracted.get("name", "deck"),
        "members": members[:48],
        "lives": lives[:12],
        "initial_deck": initial_deck,
        "energy": energy[:12],
    }


def load_tournament_decks(full_db: dict, deck_source: str | Path) -> list[dict[str, object]]:
    parser = UnifiedDeckParser(full_db)
    source_path = Path(deck_source)
    if not source_path.is_absolute():
        source_path = ROOT_DIR / source_path

    deck_files = sorted(source_path.glob("*.txt")) if source_path.is_dir() else [source_path]
    decks: list[dict[str, object]] = []
    for deck_file in deck_files:
        extracted_decks = parser.extract_from_content(deck_file.read_text(encoding="utf-8"))
        for extracted in extracted_decks:
            try:
                deck = _resolve_deck_codes(parser, extracted)
            except ValueError:
                continue
            if deck_file.is_relative_to(ROOT_DIR):
                deck["source"] = str(deck_file.relative_to(ROOT_DIR))
            else:
                deck["source"] = str(deck_file)
            decks.append(deck)
    if not decks:
        raise ValueError(f"No usable decks found at {source_path}")
    return decks


def _apply_observation_mode(obs: np.ndarray, mode: str) -> np.ndarray:
    if mode == OBSERVATION_MODE_FULL:
        return np.asarray(obs, dtype=np.float32)
    if mode not in {OBSERVATION_MODE_HINT, OBSERVATION_MODE_RAW}:
        raise ValueError(f"Unknown observation mode: {mode}")

    view = np.array(obs, dtype=np.float32, copy=True)

    for card_idx in range(VANILLA_TOTAL_CARDS):
        base = CARD_BLOCK_START + card_idx * CARD_BLOCK
        if mode == OBSERVATION_MODE_RAW:
            view[base + CARD_INDIVIDUAL_PROB_OFFSET] = 0.0
        view[base + CARD_PARTICIPATION_OFFSET] = 0.0
    if mode == OBSERVATION_MODE_RAW:
        view[GLOBAL_PORTFOLIO_START:GLOBAL_PORTFOLIO_END] = 0.0
    return view


def build_state_observation(state: engine_rust.PyGameState, observation_mode: str) -> np.ndarray:
    obs = np.asarray(state.to_vanilla_tensor(), dtype=np.float32)
    if obs.shape[0] != VANILLA_INPUT_DIM:
        raise ValueError(f"Expected vanilla tensor length {VANILLA_INPUT_DIM}, got {obs.shape[0]}")
    return _apply_observation_mode(obs, observation_mode)


def _load_checkpoint_into_model(model: nn.Module, checkpoint: dict[str, object]) -> None:
    state_dict = checkpoint.get("model") if isinstance(checkpoint, dict) and "model" in checkpoint else checkpoint
    model.load_state_dict(state_dict)


def _resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def _clear_training_state(config: OvernightConfig) -> None:
    checkpoint_dir = _resolve_path(config.checkpoint_dir)
    buffer_dir = _resolve_path(config.buffer_dir)
    for target in (checkpoint_dir, buffer_dir):
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
    for file_target in (
        _resolve_path(config.log_csv),
        _resolve_path(config.benchmark_log_csv),
        _resolve_path(config.proof_log_csv),
        _resolve_path(config.proof_output_json),
    ):
        if file_target.exists():
            try:
                file_target.unlink()
            except Exception:
                pass


def _apply_deterministic_setup(state: engine_rust.PyGameState, rust_db: engine_rust.PyCardDatabase) -> None:
    safety = 0
    while not state.is_terminal() and safety < 8:
        legal_ids = [int(action_id) for action_id in state.get_legal_action_ids()]
        if not legal_ids:
            state.auto_step(rust_db)
            safety += 1
            continue
        phase = int(state.phase)
        if phase in (PHASE_RPS, PHASE_TURN_ORDER):
            state.step(min(legal_ids))
            state.auto_step(rust_db)
            safety += 1
            continue
        break


def _policy_from_suggestions(
    player_json: dict,
    suggestions: Sequence[tuple[int, float, int]],
    initial_deck: Sequence[int],
    phase: int,
    legal_mask: np.ndarray,
) -> np.ndarray:
    dense = sparse_policy_from_engine_visits(player_json, suggestions, initial_deck, phase)
    if dense.sum() <= 0:
        dense = legal_mask.astype(np.float32)
        dense /= max(dense.sum(), 1.0)
    return dense.astype(np.float32)


def _rounded(value: object, digits: int = 4) -> object:
    if isinstance(value, float):
        return round(value, digits)
    if isinstance(value, dict):
        return {key: _rounded(subvalue, digits) for key, subvalue in value.items()}
    if isinstance(value, list):
        return [_rounded(item, digits) for item in value]
    return value


def _player_metrics_from_state_json(state_json: dict, player_idx: int) -> tuple[int, int]:
    player_json = state_json["players"][player_idx]
    return int(player_json["score"]), len(player_json.get("success_lives", []))


def _compute_shaped_value_target(
    record: dict[str, object],
    winner: int,
    terminal_turn: int,
    max_turns: int,
    final_scores: tuple[int, int],
    final_lives: tuple[int, int],
    fast_win_turn_threshold: int,
) -> float:
    player = int(record["player"])
    record_turn = int(record.get("turn", terminal_turn))
    base_value = perspective_fast_win_value(
        player=player,
        winner=winner,
        turns=int(terminal_turn),
        max_turns=max_turns,
        final_scores=final_scores,
        final_lives=final_lives,
        fast_win_turn_threshold=fast_win_turn_threshold,
    )
    action_turn_frac = max(0.0, (max_turns - min(record_turn, max_turns)) / max(1, max_turns))
    immediate_live_bonus = (
        float(record.get("immediate_live_gain", 0.0))
        * VALUE_IMMEDIATE_LIVE_BONUS
        * (1.0 + VALUE_IMMEDIATE_LIVE_TURN_SCALE * action_turn_frac)
    )
    immediate_score_bonus = (
        min(float(record.get("immediate_score_gain", 0.0)) / 3.0, 1.0)
        * VALUE_IMMEDIATE_SCORE_BONUS
        * (1.0 + VALUE_IMMEDIATE_SCORE_TURN_SCALE * action_turn_frac)
    )
    setup_progress_bonus = max(0.0, float(record.get("setup_progress_gain", 0.0))) * VALUE_SETUP_PROGRESS_WEIGHT * (1.0 + 0.5 * action_turn_frac)
    coverage_bonus = max(0.0, float(record.get("coverage_gain", 0.0))) * VALUE_COVERAGE_GAIN_WEIGHT * (1.0 + 0.5 * action_turn_frac)
    liveset_progress_bonus = max(0.0, float(record.get("live_set_gain", 0.0))) * VALUE_LIVESET_PROGRESS_WEIGHT
    baton_progress_bonus = max(0.0, float(record.get("max_stage_cost_gain", 0.0))) * VALUE_BATON_PROGRESS_WEIGHT
    contested_pass_penalty = VALUE_CONTESTED_PASS_PENALTY * action_turn_frac if record.get("contested_pass") else 0.0
    target = (
        base_value
        + immediate_live_bonus
        + immediate_score_bonus
        + setup_progress_bonus
        + coverage_bonus
        + liveset_progress_bonus
        + baton_progress_bonus
        - contested_pass_penalty
    )
    return float(target)


class VanillaSelfPlayTrainer:
    def __init__(self, config: OvernightConfig):
        _configure_logging()
        _configure_torch_runtime()
        self.config = self._tune_config_for_hardware(copy.deepcopy(config))
        _seed_everything(config.seed)
        self.device = torch.device(self.config.device)
        if self.device.type == "cuda" and not torch.cuda.is_available():
            workspace_venv = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
            hint = f" Run with {workspace_venv}." if workspace_venv.exists() else ""
            raise RuntimeError("CUDA was requested but the active interpreter does not provide CUDA Torch." + hint)
        self.amp_enabled = self.device.type == "cuda"
        self.autocast_device = self.device.type if self.device.type in {"cuda", "cpu"} else "cpu"

        if self.config.reset_training_state:
            _clear_training_state(self.config)

        self.checkpoint_dir = ROOT_DIR / self.config.checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.best_checkpoint_path = self.checkpoint_dir / self.config.best_checkpoint_name
        self.log_csv_path = ROOT_DIR / self.config.log_csv
        self.log_csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.benchmark_log_csv_path = ROOT_DIR / self.config.benchmark_log_csv
        self.benchmark_log_csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.proof_log_csv_path = ROOT_DIR / self.config.proof_log_csv
        self.proof_log_csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.proof_output_json_path = ROOT_DIR / self.config.proof_output_json
        self.proof_output_json_path.parent.mkdir(parents=True, exist_ok=True)
        self._resume_checkpoint = self._load_resume_checkpoint()
        self._stop_requested = False

        full_db, db_json = load_vanilla_database_json(self.config.db_path)
        self.full_db = full_db
        self.member_card_lookup = {int(card_id): card for card_id, card in full_db.get("member_db", {}).items()}
        self.live_card_lookup = {int(card_id): card for card_id, card in full_db.get("live_db", {}).items()}
        self.rust_db = engine_rust.PyCardDatabase(db_json)
        self.decks = load_tournament_decks(full_db, self.config.deck_source)
        self.deck = self.decks[0]
        self.initial_deck = self.deck["initial_deck"]

        checkpoint_model_config = None
        if isinstance(self._resume_checkpoint, dict):
            checkpoint_model_config = self._resume_checkpoint.get("model_config")
        if isinstance(checkpoint_model_config, dict):
            self.model_config = VanillaTransformerConfig(**checkpoint_model_config)
        else:
            self.model_config = VanillaTransformerConfig.from_preset(
                self.config.model_preset,
                input_dim=VANILLA_INPUT_DIM,
                global_dim=VANILLA_GLOBAL_FEATURES,
                total_cards=VANILLA_TOTAL_CARDS,
                card_features=VANILLA_CARD_FEATURES,
                num_actions=ACTION_SPACE,
                value_dim=self.config.value_dim,
            )
        self.model = VanillaPolicyModel(config=self.model_config).to(self.device)
        self.model.eval()
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )
        self.scaler = torch.amp.GradScaler("cuda", enabled=self.amp_enabled)
        buffer_dir = ROOT_DIR / self.config.buffer_dir
        buffer_dir.mkdir(parents=True, exist_ok=True)
        self.buffer = PersistentBuffer(
            buffer_dir,
            self.config.buffer_size,
            VANILLA_INPUT_DIM,
            ACTION_SPACE,
            value_dim=self.config.value_dim,
        )
        self.iteration = 0
        self._maybe_load_checkpoint()
        self._initialize_best_checkpoint()
        self.alpha_evaluator = self._maybe_create_alpha_evaluator(self.model)
        self.reference_model = self._maybe_create_reference_model()
        self.reference_alpha_evaluator = self._maybe_create_alpha_evaluator(self.reference_model)
        self._activate_iteration_deck()
        self.focus_seed_bank = self._load_focus_seed_bank()
        self.single_seed_index = 0
        self.single_seed_iteration_count = 0
        self.single_seed_reward_history: list[float] = []
        self._restore_curriculum_state()
        if self.model_config.preset != self.config.model_preset:
            logger.info(
                "Resume checkpoint overrides requested preset: requested=%s loaded=%s",
                self.config.model_preset,
                self.model_config.preset,
            )

    def _deck_for_iteration(self, iteration: int) -> dict[str, object]:
        mode = str(self.config.deck_rotation_mode).lower()
        if mode == "single" or len(self.decks) == 1:
            return self.decks[0]
        if mode == "per_iteration":
            return self.decks[int(iteration) % len(self.decks)]
        raise ValueError(f"Unknown deck rotation mode: {self.config.deck_rotation_mode}")

    def _activate_iteration_deck(self) -> dict[str, object]:
        deck = self._deck_for_iteration(self.iteration)
        self.deck = deck
        self.initial_deck = deck["initial_deck"]
        return deck

    def _focus_seed_file_path(self) -> Path:
        path = Path(self.config.hard_seed_file)
        if not path.is_absolute():
            path = ROOT_DIR / path
        return path

    def _load_focus_seed_bank(self) -> list[int]:
        path = self._focus_seed_file_path()
        if not path.exists():
            if str(self.config.selfplay_seed_mode).lower() != "random":
                logger.warning("Hard seed file %s does not exist; focus modes will be unavailable", path)
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to read hard seed file %s: %s", path, exc)
            return []
        raw_seeds = payload.get("seeds", payload) if isinstance(payload, dict) else payload
        if not isinstance(raw_seeds, list):
            logger.warning("Hard seed file %s does not contain a seed list", path)
            return []
        seeds: list[int] = []
        for seed in raw_seeds:
            try:
                seeds.append(int(seed))
            except Exception:
                continue
        return seeds

    def _restore_curriculum_state(self) -> None:
        if not isinstance(self._resume_checkpoint, dict):
            return
        payload = self._resume_checkpoint.get("curriculum_state")
        if not isinstance(payload, dict):
            return
        self.single_seed_index = max(0, int(payload.get("single_seed_index", 0)))
        self.single_seed_iteration_count = max(0, int(payload.get("single_seed_iteration_count", 0)))
        raw_history = payload.get("single_seed_reward_history", [])
        if isinstance(raw_history, list):
            self.single_seed_reward_history = [float(value) for value in raw_history[-32:]]

    def _single_seed_candidates(self) -> list[int]:
        if self.focus_seed_bank:
            return self.focus_seed_bank
        return []

    def _current_single_seed(self) -> int:
        if str(self.config.selfplay_seed_mode).lower() == "fixed_single":
            return int(self.config.seed)
        candidates = self._single_seed_candidates()
        if candidates:
            return int(candidates[self.single_seed_index % len(candidates)])
        return int(self.config.seed + self.single_seed_index)

    def _uses_single_seed_eval(self) -> bool:
        return str(self.config.selfplay_seed_mode).lower() in {"curriculum_single", "fixed_single"}

    def _game_reward_breakdown(self, game_result: SelfPlayGameResult) -> CompetitiveGameRewardBreakdown:
        return competitive_fast_win_reward(
            winner=int(game_result.winner),
            turns=int(game_result.turns),
            max_turns=int(self.config.max_turns),
            final_scores=(int(game_result.p0_score), int(game_result.p1_score)),
            final_lives=(int(game_result.p0_lives), int(game_result.p1_lives)),
            fast_win_turn_threshold=int(self.config.single_seed_fast_turn_threshold),
        )

    def _evaluate_current_single_seed(self) -> SeedCertificationSummary:
        seed = self._current_single_seed()
        rows: list[dict[str, int | float]] = []
        eval_games = max(1, int(self.config.curriculum_eval_games))
        for _ in range(eval_games):
            result = self.play_self_play_game(seed)
            rows.append(
                {
                    "winner": int(result.winner),
                    "turns": int(result.turns),
                    "p0_score": int(result.p0_score),
                    "p1_score": int(result.p1_score),
                    "p0_lives": int(result.p0_lives),
                    "p1_lives": int(result.p1_lives),
                }
            )
        return summarize_seed_certification(
            rows,
            max_turns=int(self.config.max_turns),
            fast_win_turn_threshold=int(self.config.single_seed_fast_turn_threshold),
        )

    def _maybe_advance_single_seed(self, summary: SeedCertificationSummary, certified: bool) -> bool:
        self.single_seed_iteration_count += 1
        self.single_seed_reward_history.append(float(summary.avg_reward))
        ready = self.single_seed_iteration_count >= self.config.single_seed_min_iters and certified
        exhausted = self.single_seed_iteration_count >= self.config.single_seed_max_iters
        if not (ready or exhausted):
            return False
        self.single_seed_index += 1
        self.single_seed_iteration_count = 0
        self.single_seed_reward_history = []
        return True

    def _choose_self_play_seed(self, game_idx: int, seed_offset: int = 0) -> tuple[int, bool]:
        random_seed = self.config.seed + seed_offset + game_idx + self.iteration * 10_000
        mode = str(self.config.selfplay_seed_mode).lower()
        if mode == "random":
            return int(random_seed), False
        if mode == "fixed_single":
            return int(self.config.seed), True
        if mode == "curriculum_single":
            return self._current_single_seed(), True
        if not self.focus_seed_bank:
            if mode == "focus_only":
                raise RuntimeError(f"selfplay_seed_mode=focus_only requires a non-empty hard seed file at {self._focus_seed_file_path()}")
            return int(random_seed), False
        if mode not in {"focus_mix", "focus_only"}:
            raise ValueError(f"Unknown selfplay seed mode: {self.config.selfplay_seed_mode}")
        use_focus = mode == "focus_only"
        if mode == "focus_mix":
            cycle = max(1, int(round(1.0 / max(1e-6, float(self.config.hard_seed_ratio)))))
            use_focus = (game_idx % cycle) == 0
        if not use_focus:
            return int(random_seed), False
        focus_index = (self.iteration * max(1, self.config.games_per_iteration) + game_idx) % len(self.focus_seed_bank)
        return int(self.focus_seed_bank[focus_index]), True

    def _load_resume_checkpoint(self) -> dict[str, object] | None:
        latest = self.checkpoint_dir / "latest.pt"
        if not latest.exists():
            return None
        try:
            return torch.load(latest, map_location="cpu")
        except Exception as exc:
            logger.warning("Failed to read checkpoint metadata from %s: %s", latest, exc)
            return None

    def _tune_config_for_hardware(self, config: OvernightConfig) -> OvernightConfig:
        config.search_sims = max(1, int(config.search_sims))
        config.neural_mcts_batch_size = max(1, min(int(config.neural_mcts_batch_size), int(config.search_sims)))
        config.benchmark_search_sims = max(1, int(config.benchmark_search_sims))
        config.benchmark_model_search_sims = int(config.benchmark_model_search_sims)
        config.reference_benchmark_games = max(0, int(config.reference_benchmark_games))
        config.target_replay_ratio = max(0.0, float(config.target_replay_ratio))
        config.reference_promote_threshold = min(max(float(config.reference_promote_threshold), 0.0), 1.0)
        config.reference_rollback_threshold = min(max(float(config.reference_rollback_threshold), 0.0), 1.0)
        config.hard_seed_ratio = min(max(float(config.hard_seed_ratio), 0.0), 1.0)
        config.hard_seed_scan_games = max(1, int(config.hard_seed_scan_games))
        config.hard_seed_min_turns = max(1, int(config.hard_seed_min_turns))
        config.single_seed_plateau_window = max(2, int(config.single_seed_plateau_window))
        config.single_seed_plateau_delta = max(0.0, float(config.single_seed_plateau_delta))
        config.single_seed_min_iters = max(1, int(config.single_seed_min_iters))
        config.single_seed_max_iters = max(config.single_seed_min_iters, int(config.single_seed_max_iters))
        config.curriculum_eval_games = max(1, int(config.curriculum_eval_games))
        config.single_seed_target_reward = max(0.0, float(config.single_seed_target_reward))
        config.single_seed_target_decisive_rate = min(max(float(config.single_seed_target_decisive_rate), 0.0), 1.0)
        config.single_seed_target_fast_win_rate = min(max(float(config.single_seed_target_fast_win_rate), 0.0), 1.0)
        config.single_seed_target_avg_turns = max(1.0, float(config.single_seed_target_avg_turns))
        config.single_seed_fast_turn_threshold = max(1, min(int(config.single_seed_fast_turn_threshold), int(config.max_turns)))
        config.proof_eval_games = max(1, int(config.proof_eval_games))
        config.selfplay_action_source = str(config.selfplay_action_source).lower().strip()
        if config.selfplay_action_source not in {"search_sample", "search_greedy", "model_sample", "model_greedy", "hybrid_teacher"}:
            raise ValueError(f"Unknown selfplay_action_source: {config.selfplay_action_source}")
        if config.device != "cuda" or not torch.cuda.is_available():
            return config

        total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        if total_vram_gb <= 5.0:
            if config.model_preset == "small":
                logger.warning(
                    "Low-VRAM GPU detected (%.1f GB); downgrading model preset from small to tiny for stability",
                    total_vram_gb,
                )
                config.model_preset = "tiny"
            config.batch_size = min(config.batch_size, 2048)
            config.search_sims = min(config.search_sims, 12)
            config.neural_mcts_batch_size = min(config.neural_mcts_batch_size, config.search_sims, 12)
            config.games_per_iteration = min(config.games_per_iteration, 40)
            config.training_steps_per_iteration = min(config.training_steps_per_iteration, 24)
        elif total_vram_gb <= 9.0:
            config.batch_size = min(config.batch_size, 4096)
            config.search_sims = min(config.search_sims, 24)
            config.neural_mcts_batch_size = min(config.neural_mcts_batch_size, config.search_sims, 16)
        else:
            config.neural_mcts_batch_size = min(config.neural_mcts_batch_size, config.search_sims, 24)
        config.games_per_iteration = max(1, int(config.games_per_iteration))
        config.training_steps_per_iteration = max(1, int(config.training_steps_per_iteration))
        return config

    def _load_best_checkpoint(self) -> dict[str, object] | None:
        if not self.best_checkpoint_path.exists():
            return None
        try:
            return torch.load(self.best_checkpoint_path, map_location="cpu")
        except Exception as exc:
            logger.warning("Failed to read best checkpoint metadata from %s: %s", self.best_checkpoint_path, exc)
            return None

    def _initialize_best_checkpoint(self) -> None:
        if self.best_checkpoint_path.exists():
            return
        payload = {
            "model": self.model.state_dict(),
            "model_config": asdict(self.model_config),
            "iteration": self.iteration,
            "completed_iteration": self.iteration,
            "next_iteration": self.iteration,
            "save_reason": "best_init",
            "saved_at_unix": time.time(),
        }
        self._atomic_torch_save(payload, self.best_checkpoint_path)

    def _reference_checkpoint_payload(self) -> dict[str, object] | None:
        best_checkpoint = self._load_best_checkpoint()
        if best_checkpoint is not None:
            return best_checkpoint
        return self._resume_checkpoint

    def _effective_benchmark_model_search_sims(self) -> int:
        requested = int(self.config.benchmark_model_search_sims)
        if requested <= 0:
            return int(self.config.search_sims)
        return max(1, requested)

    def _effective_benchmark_search_sims(self) -> int:
        return max(1, int(self.config.benchmark_search_sims))

    def _uses_search_targets(self) -> bool:
        return str(self.config.training_target_mode).lower() == "search"

    def _uses_neural_mcts_targets(self) -> bool:
        return str(self.config.training_target_mode).lower() == "neural_mcts"

    def _maybe_create_alpha_evaluator(self, model: nn.Module | None):
        if not self._uses_neural_mcts_targets() or model is None:
            return None
        if not hasattr(engine_rust, "PyAlphaZeroEvaluator") or not hasattr(engine_rust, "AlphaZeroTensorType"):
            raise RuntimeError(
                "training_target_mode=neural_mcts requires engine_rust.PyAlphaZeroEvaluator and AlphaZeroTensorType. Rebuild/install the Rust extension with extension-module support."
            )
        return engine_rust.PyAlphaZeroEvaluator(model, engine_rust.AlphaZeroTensorType.Vanilla)

    def _maybe_create_reference_model(self) -> nn.Module | None:
        reference_checkpoint = self._reference_checkpoint_payload()
        if reference_checkpoint is None:
            return None
        reference_model = VanillaPolicyModel(config=self.model_config).to(self.device)
        _load_checkpoint_into_model(reference_model, reference_checkpoint)
        reference_model.eval()
        for parameter in reference_model.parameters():
            parameter.requires_grad_(False)
        return reference_model

    def _refresh_reference_state(self) -> None:
        self.reference_model = self._maybe_create_reference_model()
        self.reference_alpha_evaluator = self._maybe_create_alpha_evaluator(self.reference_model)

    def _rebuild_optimizer(self) -> None:
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )
        self.scaler = torch.amp.GradScaler("cuda", enabled=self.amp_enabled)

    def _reference_match_score(self, summary: dict[str, float | int]) -> float:
        games = max(1.0, float(summary.get("games", 0)))
        wins = float(summary.get("model_wins", 0))
        draws = float(summary.get("draws", 0))
        return (wins + 0.5 * draws) / games

    def _promote_current_as_best(self, reason: str, score: float) -> None:
        payload = {
            "model": self.model.state_dict(),
            "model_config": asdict(self.model_config),
            "iteration": self.iteration,
            "completed_iteration": self.iteration,
            "next_iteration": self.iteration,
            "save_reason": reason,
            "reference_score": score,
            "saved_at_unix": time.time(),
        }
        self._atomic_torch_save(payload, self.best_checkpoint_path)
        self._refresh_reference_state()

    def _rollback_to_best(self, reason: str, score: float) -> None:
        best_checkpoint = self._load_best_checkpoint()
        if best_checkpoint is None:
            return
        _load_checkpoint_into_model(self.model, best_checkpoint)
        self.model.eval()
        self._rebuild_optimizer()
        self.alpha_evaluator = self._maybe_create_alpha_evaluator(self.model)
        self._refresh_reference_state()
        logger.warning("Rolled back current model to best checkpoint: reason=%s reference_score=%.3f", reason, score)
        self._save_checkpoint(reason=reason, advance_iteration=False)

    def _maybe_promote_or_rollback(self, suite: dict[str, dict[str, float | int]]) -> None:
        reference = suite.get("vs_reference")
        if not isinstance(reference, dict):
            return
        score = self._reference_match_score(reference)
        if score >= self.config.reference_promote_threshold:
            logger.info("Promoting current model to best checkpoint: reference_score=%.3f threshold=%.3f", score, self.config.reference_promote_threshold)
            self._promote_current_as_best("benchmark_promote", score)
            return
        if self.config.rollback_on_reference_regression and score <= self.config.reference_rollback_threshold:
            self._rollback_to_best("benchmark_rollback", score)

    def _teacher_action_probability(self) -> float:
        if not self._uses_search_targets():
            return 0.0
        if self.buffer.count < self.config.min_buffer_items:
            return 1.0
        if self.iteration < self.config.teacher_action_warmup_iters:
            return self.config.teacher_action_prob
        decay_span = max(1, self.config.teacher_action_decay_iters)
        progress = min(1.0, (self.iteration - self.config.teacher_action_warmup_iters) / decay_span)
        start = self.config.teacher_action_prob
        end = self.config.min_teacher_action_prob
        return float(start + (end - start) * progress)

    def _select_execution_policy(
        self,
        model_probs: np.ndarray,
        target_policy: np.ndarray,
        legal_policy_ids: np.ndarray,
        teacher_action_prob: float,
        rng: random.Random,
    ) -> np.ndarray:
        if len(legal_policy_ids) <= 1:
            return target_policy
        if rng.random() < teacher_action_prob:
            return target_policy
        return model_probs

    def _maybe_load_checkpoint(self) -> None:
        checkpoint = self._resume_checkpoint
        if checkpoint is None:
            return
        _load_checkpoint_into_model(self.model, checkpoint)
        if checkpoint.get("optimizer"):
            try:
                self.optimizer.load_state_dict(checkpoint["optimizer"])
            except Exception as exc:
                logger.warning("Failed to load optimizer state from checkpoint: %s", exc)
        self.iteration = int(checkpoint.get("next_iteration", int(checkpoint.get("iteration", 0)) + 1))
        logger.info(
            "Loaded checkpoint: completed_iteration=%s next_iteration=%s preset=%s",
            checkpoint.get("iteration", -1),
            self.iteration,
            self.model_config.preset,
        )

    def _atomic_torch_save(self, payload: dict[str, object], path: Path) -> None:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        torch.save(payload, tmp_path)
        tmp_path.replace(path)

    def _flush_handle(self, handle) -> None:
        handle.flush()
        os.fsync(handle.fileno())

    def _ensure_csv_schema(self, path: Path, fieldnames: Sequence[str]) -> None:
        if not path.exists():
            return
        expected_header = ",".join(fieldnames)
        with path.open("r", encoding="utf-8", newline="") as handle:
            existing_header = handle.readline().strip()
        if existing_header == expected_header:
            return
        backup = path.with_name(f"{path.stem}.schema_backup_{int(time.time())}{path.suffix}")
        path.replace(backup)
        logger.warning("Rotated %s to %s due to CSV schema change", path.name, backup.name)

    def _save_checkpoint(self, *, reason: str = "iteration", advance_iteration: bool = True) -> None:
        self.buffer.flush()
        payload = {
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "iteration": self.iteration,
            "completed_iteration": self.iteration,
            "next_iteration": self.iteration + 1 if advance_iteration else self.iteration,
            "model_config": asdict(self.model_config),
            "trainer_config": asdict(self.config),
            "curriculum_state": {
                "single_seed_index": int(self.single_seed_index),
                "single_seed_iteration_count": int(self.single_seed_iteration_count),
                "single_seed_reward_history": [float(value) for value in self.single_seed_reward_history[-32:]],
            },
            "save_reason": reason,
            "saved_at_unix": time.time(),
        }
        self._atomic_torch_save(payload, self.checkpoint_dir / "latest.pt")
        self._atomic_torch_save(payload, self.checkpoint_dir / f"iter_{self.iteration:05d}.pt")

    def _append_log_row(self, row: dict[str, object]) -> None:
        self._ensure_csv_schema(self.log_csv_path, list(row.keys()))
        write_header = not self.log_csv_path.exists()
        with self.log_csv_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
            if write_header:
                writer.writeheader()
            writer.writerow(row)
            self._flush_handle(handle)

    def _append_benchmark_row(self, row: dict[str, object]) -> None:
        self._ensure_csv_schema(self.benchmark_log_csv_path, list(row.keys()))
        write_header = not self.benchmark_log_csv_path.exists()
        with self.benchmark_log_csv_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
            if write_header:
                writer.writeheader()
            writer.writerow(row)
            self._flush_handle(handle)

    def _append_proof_row(self, row: dict[str, object]) -> None:
        self._ensure_csv_schema(self.proof_log_csv_path, list(row.keys()))
        write_header = not self.proof_log_csv_path.exists()
        with self.proof_log_csv_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
            if write_header:
                writer.writeheader()
            writer.writerow(row)
            self._flush_handle(handle)

    def _new_state(self, seed: int) -> engine_rust.PyGameState:
        state = engine_rust.PyGameState(self.rust_db)
        state.initialize_game_with_seed(
            self.deck["initial_deck"],
            self.deck["initial_deck"],
            self.deck["energy"],
            self.deck["energy"],
            [],
            [],
            int(seed),
        )
        state.silent = True
        state.debug_mode = False
        return state

    def _model_inference_with(self, model: nn.Module, obs: np.ndarray, legal_mask: np.ndarray) -> tuple[np.ndarray, float]:
        obs_t = torch.from_numpy(obs).unsqueeze(0).to(self.device)
        mask_t = torch.from_numpy(legal_mask).unsqueeze(0).to(self.device)
        with torch.inference_mode():
            logits, value = model(obs_t, mask=mask_t)
            probs = torch.softmax(logits, dim=1)[0].cpu().numpy().astype(np.float32)
            value_scalar = float(value[0, 0].item())
        return probs, value_scalar

    def _model_inference(self, obs: np.ndarray, legal_mask: np.ndarray) -> tuple[np.ndarray, float]:
        return self._model_inference_with(self.model, obs, legal_mask)

    def _one_hot_policy(self, policy_id: int) -> np.ndarray:
        policy = np.zeros(ACTION_SPACE, dtype=np.float32)
        policy[int(policy_id)] = 1.0
        return policy

    def _choose_policy_action(
        self,
        probs: np.ndarray,
        legal_policy_ids: np.ndarray,
        temperature: float,
        epsilon: float,
        rng: random.Random,
    ) -> int:
        if len(legal_policy_ids) == 1:
            return int(legal_policy_ids[0])
        if rng.random() < epsilon:
            return int(rng.choice(legal_policy_ids.tolist()))
        legal_probs = probs[legal_policy_ids].astype(np.float64)
        if temperature > 1e-3:
            legal_probs = np.power(np.maximum(legal_probs, 1e-8), 1.0 / temperature)
        if legal_probs.sum() <= 0:
            legal_probs = np.ones_like(legal_probs)
        legal_probs /= legal_probs.sum()
        return int(rng.choices(legal_policy_ids.tolist(), weights=legal_probs.tolist(), k=1)[0])

    def _argmax_policy_action(self, probs: np.ndarray, legal_policy_ids: np.ndarray) -> int:
        if len(legal_policy_ids) == 1:
            return int(legal_policy_ids[0])
        return int(legal_policy_ids[np.argmax(probs[legal_policy_ids])])

    def _choose_model_eval_action_with_model(
        self,
        state: engine_rust.PyGameState,
        legal_ids: Sequence[int],
        model: nn.Module,
    ) -> int:
        phase = int(state.phase)
        if phase in (PHASE_RPS, PHASE_TURN_ORDER):
            return int(min(legal_ids))
        legal_mask, legal_policy_ids, mapping = build_legal_policy_context(legal_ids, self.initial_deck, phase)
        if len(legal_policy_ids) == 0:
            return int(legal_ids[0])
        obs = build_state_observation(state, self.config.observation_mode)
        probs, _ = self._model_inference_with(model, obs, legal_mask)
        choice = int(legal_policy_ids[np.argmax(probs[legal_policy_ids])])
        return int(mapping.get(choice, legal_ids[0]))

    def _choose_model_eval_action(self, state: engine_rust.PyGameState, legal_ids: Sequence[int]) -> int:
        return self._choose_model_eval_action_with_model(state, legal_ids, self.model)

    def _search_neural_mcts_with(
        self,
        state: engine_rust.PyGameState,
        evaluator,
        search_sims: int,
    ) -> list[tuple[int, float, int]]:
        if evaluator is None:
            raise RuntimeError("Neural MCTS requested but AlphaZero evaluator is not initialized")
        batch_size = max(1, min(int(self.config.neural_mcts_batch_size), int(search_sims)))
        return state.search_mcts_alphazero(
            int(search_sims),
            evaluator,
            batch_size,
        )

    def _search_neural_mcts(self, state: engine_rust.PyGameState) -> list[tuple[int, float, int]]:
        return self._search_neural_mcts_with(state, self.alpha_evaluator, self.config.search_sims)

    def _choose_neural_mcts_action_with_context(
        self,
        state: engine_rust.PyGameState,
        legal_ids: Sequence[int],
        evaluator,
        search_sims: int,
    ) -> int:
        phase = int(state.phase)
        if phase in (PHASE_RPS, PHASE_TURN_ORDER):
            return int(min(legal_ids))
        if len(legal_ids) == 1:
            return int(legal_ids[0])
        suggestions = self._rerank_neural_suggestions(
            state,
            self._search_neural_mcts_with(state, evaluator, search_sims),
        )
        return int(suggestions[0][0]) if suggestions else int(legal_ids[0])

    def _choose_neural_mcts_action(self, state: engine_rust.PyGameState, legal_ids: Sequence[int]) -> int:
        return self._choose_neural_mcts_action_with_context(state, legal_ids, self.alpha_evaluator, self.config.search_sims)

    def _choose_search_action(
        self,
        state: engine_rust.PyGameState,
        legal_ids: Sequence[int],
        search_sims: int | None = None,
    ) -> int:
        phase = int(state.phase)
        if phase in (PHASE_RPS, PHASE_TURN_ORDER):
            return int(min(legal_ids))
        if len(legal_ids) == 1:
            return int(legal_ids[0])
        suggestions = state.get_mcts_suggestions(int(search_sims or self.config.search_sims))
        return int(suggestions[0][0]) if suggestions else int(legal_ids[0])

    def _choose_reference_action(
        self,
        state: engine_rust.PyGameState,
        legal_ids: Sequence[int],
        search_sims: int,
    ) -> int:
        if self.reference_model is None:
            raise RuntimeError("Reference benchmark requested without a reference checkpoint model")
        if self._uses_neural_mcts_targets():
            return self._choose_neural_mcts_action_with_context(
                state,
                legal_ids,
                self.reference_alpha_evaluator,
                search_sims,
            )
        return self._choose_model_eval_action_with_model(state, legal_ids, self.reference_model)

    def _choose_greedy_action(self, state: engine_rust.PyGameState, legal_ids: Sequence[int]) -> int:
        phase = int(state.phase)
        if phase in (PHASE_RPS, PHASE_TURN_ORDER):
            return int(min(legal_ids))
        player = int(state.current_player)
        try:
            action = int(state.get_greedy_action(self.rust_db, player, 0, None))
        except Exception:
            action = int(legal_ids[0])
        if action not in legal_ids:
            action = int(legal_ids[0])
        return action

    def _choose_turnseq_action(self, state: engine_rust.PyGameState, legal_ids: Sequence[int]) -> int:
        phase = int(state.phase)
        if phase in (PHASE_RPS, PHASE_TURN_ORDER):
            return int(min(legal_ids))
        try:
            _, action_seq, _, _, _ = state.plan_full_turn_with_stats(self.rust_db)
        except Exception:
            action_seq = []
        if action_seq:
            action = int(action_seq[0])
            if action in legal_ids:
                return action
        return int(legal_ids[0])

    def _simulate_action_outcome(
        self,
        state: engine_rust.PyGameState,
        action: int,
        acting_player: int,
        before_json: dict | None = None,
    ) -> dict[str, object]:
        before_state = before_json if before_json is not None else json.loads(state.to_json())
        before_score, before_lives = _player_metrics_from_state_json(before_state, acting_player)
        sim = _clone_state(state, self.rust_db)
        sim.step(int(action))
        sim.auto_step(self.rust_db)
        after_state = json.loads(sim.to_json())
        after_score, after_lives = _player_metrics_from_state_json(after_state, acting_player)
        progress = self._strategic_progress_delta(before_state, after_state, acting_player)
        return {
            "score_gain": after_score - before_score,
            "live_gain": after_lives - before_lives,
            "turn_after": int(sim.turn),
            "winner_after": int(sim.get_winner()) if sim.is_terminal() else -1,
            **progress,
        }

    def _player_progress_snapshot(self, state_json: dict, player_idx: int) -> dict[str, float]:
        player_json = state_json["players"][player_idx]
        stage_ids = [int(card_id) for card_id in player_json.get("stage", []) if int(card_id) >= 0]
        live_ids = [int(card_id) for card_id in player_json.get("live_zone", []) if int(card_id) >= 0]
        stage_hearts = np.zeros(7, dtype=np.float32)
        live_required = np.zeros(7, dtype=np.float32)
        total_stage_cost = 0.0
        max_stage_cost = 0.0
        total_stage_blades = 0.0
        total_live_score = 0.0

        for card_id in stage_ids:
            member = self.member_card_lookup.get(card_id)
            if not member:
                continue
            stage_hearts += np.asarray(member.get("hearts", [0, 0, 0, 0, 0, 0, 0]), dtype=np.float32)
            cost = float(member.get("cost", 0.0))
            blades = float(member.get("blades", 0.0))
            total_stage_cost += cost
            max_stage_cost = max(max_stage_cost, cost)
            total_stage_blades += blades

        for card_id in live_ids:
            live = self.live_card_lookup.get(card_id)
            if not live:
                continue
            live_required += np.asarray(live.get("required_hearts", [0, 0, 0, 0, 0, 0, 0]), dtype=np.float32)
            total_live_score += float(live.get("score", 0.0))

        total_required = float(live_required.sum())
        matched_hearts = float(np.minimum(stage_hearts, live_required).sum())
        coverage = matched_hearts / max(total_required, 1.0)
        setup_value = (
            0.55 * coverage * (1.0 + min(total_live_score, 9.0) / 9.0)
            + 0.05 * float(len(live_ids))
            + 0.015 * total_stage_cost
            + 0.02 * max_stage_cost
            + 0.01 * min(total_stage_blades, 15.0)
            + 0.01 * float(len(stage_ids))
        )
        return {
            "coverage": float(np.clip(coverage, 0.0, 1.0)),
            "setup_value": float(np.clip(setup_value, 0.0, 2.0)),
            "live_slots": float(len(live_ids)),
            "max_stage_cost": float(max_stage_cost),
        }

    def _strategic_progress_delta(self, before_state_json: dict, after_state_json: dict, player_idx: int) -> dict[str, float]:
        before = self._player_progress_snapshot(before_state_json, player_idx)
        after = self._player_progress_snapshot(after_state_json, player_idx)
        return {
            "setup_progress_gain": float(np.clip(after["setup_value"] - before["setup_value"], -1.0, 1.0)),
            "coverage_gain": float(np.clip(after["coverage"] - before["coverage"], -1.0, 1.0)),
            "live_set_gain": float(np.clip((after["live_slots"] - before["live_slots"]) / 3.0, -1.0, 1.0)),
            "max_stage_cost_gain": float(np.clip((after["max_stage_cost"] - before["max_stage_cost"]) / 20.0, -1.0, 1.0)),
        }

    def _rerank_neural_suggestions(
        self,
        state: engine_rust.PyGameState,
        suggestions: Sequence[tuple[int, float, int]],
    ) -> list[tuple[int, float, int]]:
        if len(suggestions) <= 1:
            return list(suggestions)
        top_visits = int(suggestions[0][2])
        candidate_count = min(6, len(suggestions))
        candidate_indexes = [
            idx
            for idx, (_action, _score, visits) in enumerate(suggestions[:candidate_count])
            if top_visits - int(visits) <= 1
        ]
        if len(candidate_indexes) <= 1:
            return list(suggestions)

        acting_player = int(state.current_player)
        turn_pressure = max(0.0, (self.config.max_turns - min(int(state.turn), self.config.max_turns)) / max(1, self.config.max_turns))
        ranked: list[tuple[tuple[float, ...], int, tuple[int, float, int]]] = []
        for idx in candidate_indexes:
            action, score, visits = suggestions[idx]
            rollout = self._simulate_action_outcome(state, int(action), acting_player)
            pass_penalty = 1.0 if int(action) == ACTION_BASE_PASS and int(rollout["winner_after"]) != acting_player and float(rollout.get("setup_progress_gain", 0.0)) <= 0.0 and int(rollout["live_gain"]) <= 0 else 0.0
            setup_bonus = (
                float(rollout.get("setup_progress_gain", 0.0))
                + 0.6 * float(rollout.get("coverage_gain", 0.0))
                + 0.3 * float(rollout.get("live_set_gain", 0.0))
                + 0.2 * float(rollout.get("max_stage_cost_gain", 0.0))
            ) * (1.0 + 0.5 * turn_pressure)
            key = (
                float(int(rollout["winner_after"]) == acting_player),
                float(max(0, int(rollout["live_gain"]))),
                float(setup_bonus),
                -pass_penalty,
                float(visits),
                float(score),
                -float(idx),
            )
            ranked.append((key, idx, (int(action), float(score), int(visits))))

        ranked.sort(key=lambda item: item[0], reverse=True)
        ordered = list(suggestions)
        replacement = [entry for _key, _idx, entry in ranked]
        for target_idx, replacement_entry in zip(candidate_indexes, replacement, strict=False):
            ordered[target_idx] = replacement_entry
        return ordered

    def _policy_target_from_suggestions(
        self,
        state: engine_rust.PyGameState,
        phase: int,
        legal_mask: np.ndarray,
        suggestions: Sequence[tuple[int, float, int]],
    ) -> np.ndarray:
        dense = _policy_from_suggestions({}, suggestions, self.initial_deck, phase, legal_mask)
        if dense.sum() <= 0:
            return dense
        dense /= max(float(dense.sum()), 1e-8)
        return dense.astype(np.float32)

    def _audit_legal_actions(self, state: engine_rust.PyGameState, legal_ids: Sequence[int]) -> list[dict[str, object]]:
        phase = int(state.phase)
        acting_player = int(state.current_player)
        before_json = json.loads(state.to_json())
        legal_mask, legal_policy_ids, _mapping = build_legal_policy_context(legal_ids, self.initial_deck, phase)
        obs = build_state_observation(state, self.config.observation_mode)
        probs = None
        if len(legal_policy_ids) > 0 and phase not in (PHASE_RPS, PHASE_TURN_ORDER):
            probs, _ = self._model_inference(obs, legal_mask)

        neural_map = {
            int(action): (float(score), int(visits))
            for action, score, visits in (self._search_neural_mcts(state) if self._uses_neural_mcts_targets() else [])
        }
        heuristic_map = {
            int(action): (float(score), int(visits))
            for action, score, visits in state.get_mcts_suggestions(self._effective_benchmark_search_sims())
        }
        greedy_map = {
            int(action): float(score)
            for action, score in state.get_greedy_evaluations(self.rust_db, acting_player, 0, None)
        }

        rows: list[dict[str, object]] = []
        for action in legal_ids:
            policy_id = engine_action_to_policy_id({}, int(action), self.initial_deck, phase)
            model_prob = float(probs[policy_id]) if probs is not None and 0 <= policy_id < ACTION_SPACE else None
            neural_score, neural_visits = neural_map.get(int(action), (None, 0))
            heuristic_score, heuristic_visits = heuristic_map.get(int(action), (None, 0))
            rollout = self._simulate_action_outcome(state, int(action), acting_player, before_json=before_json)
            rows.append(
                {
                    "action": int(action),
                    "label": state.get_action_label(int(action)),
                    "policy_id": int(policy_id),
                    "model_prob": model_prob,
                    "neural_score": neural_score,
                    "neural_visits": int(neural_visits),
                    "heuristic_score": heuristic_score,
                    "heuristic_visits": int(heuristic_visits),
                    "greedy_score": greedy_map.get(int(action)),
                    "score_gain": int(rollout["score_gain"]),
                    "live_gain": int(rollout["live_gain"]),
                    "winner_after": int(rollout["winner_after"]),
                }
            )
        rows.sort(
            key=lambda row: (
                -int(row.get("neural_visits") or 0),
                -float(row.get("heuristic_visits") or 0),
                -float(row.get("model_prob") or 0.0),
                -int(row.get("live_gain") or 0),
                -int(row.get("score_gain") or 0),
            )
        )
        return rows

    def audit_game(self, seed: int, max_decisions: int = 12) -> dict[str, object]:
        state = self._new_state(seed)
        _apply_deterministic_setup(state, self.rust_db)
        steps: list[dict[str, object]] = []
        decisions = 0

        while not state.is_terminal() and int(state.turn) < self.config.max_turns and decisions < max_decisions:
            legal_ids = [int(action_id) for action_id in state.get_legal_action_ids()]
            if not legal_ids:
                state.auto_step(self.rust_db)
                continue
            phase = int(state.phase)
            should_log_decision = phase >= 1
            before_json = json.loads(state.to_json())
            acting_player = int(state.current_player)
            chosen_action = (
                self._choose_neural_mcts_action(state, legal_ids)
                if self._uses_neural_mcts_targets()
                else self._choose_model_eval_action(state, legal_ids)
            )
            if should_log_decision:
                action_rows = self._audit_legal_actions(state, legal_ids)
                chosen_outcome = self._simulate_action_outcome(state, chosen_action, acting_player, before_json=before_json)
                obs = build_state_observation(state, self.config.observation_mode)
                score_now, lives_now = _player_metrics_from_state_json(before_json, acting_player)
                steps.append(
                    {
                        "turn": int(state.turn),
                        "phase": phase,
                        "player": acting_player,
                        "score": score_now,
                        "lives": lives_now,
                        "active_live_ev": float(obs[GLOBAL_ACTIVE_LIVE_EV]),
                        "clearable_now": float(obs[GLOBAL_CLEARABLE_NOW]),
                        "chosen_action": int(chosen_action),
                        "chosen_label": state.get_action_label(int(chosen_action)),
                        "chosen_contested_pass": bool(int(chosen_action) == ACTION_BASE_PASS and len(legal_ids) > 1),
                        "chosen_score_gain": int(chosen_outcome["score_gain"]),
                        "chosen_live_gain": int(chosen_outcome["live_gain"]),
                        "legal_actions": action_rows,
                    }
                )
            state.step(int(chosen_action))
            state.auto_step(self.rust_db)
            if should_log_decision:
                decisions += 1

        final_json = json.loads(state.to_json())
        return {
            "seed": seed,
            "terminal": bool(state.is_terminal()),
            "winner": int(state.get_winner()) if state.is_terminal() else -1,
            "turn": int(state.turn),
            "p0_score": int(final_json["players"][0]["score"]),
            "p1_score": int(final_json["players"][1]["score"]),
            "p0_lives": len(final_json["players"][0].get("success_lives", [])),
            "p1_lives": len(final_json["players"][1].get("success_lives", [])),
            "steps": steps,
        }

    def _play_match(
        self,
        seed: int,
        p0_agent: str,
        p1_agent: str,
        *,
        model_search_sims: int,
        opponent_search_sims: int,
    ) -> dict[str, float | int]:
        state = self._new_state(seed)
        _apply_deterministic_setup(state, self.rust_db)
        while not state.is_terminal() and int(state.turn) < self.config.max_turns:
            legal_ids = [int(action_id) for action_id in state.get_legal_action_ids()]
            if not legal_ids:
                state.auto_step(self.rust_db)
                continue
            current_player = int(state.current_player)
            agent = p0_agent if current_player == 0 else p1_agent
            if agent == "model":
                if self._uses_neural_mcts_targets():
                    action = self._choose_neural_mcts_action_with_context(
                        state,
                        legal_ids,
                        self.alpha_evaluator,
                        model_search_sims,
                    )
                else:
                    action = self._choose_model_eval_action_with_model(state, legal_ids, self.model)
            elif agent == "reference":
                action = self._choose_reference_action(state, legal_ids, model_search_sims)
            elif agent == "search":
                action = self._choose_search_action(state, legal_ids, opponent_search_sims)
            elif agent == "greedy":
                action = self._choose_greedy_action(state, legal_ids)
            elif agent == "turnseq":
                action = self._choose_turnseq_action(state, legal_ids)
            else:
                raise ValueError(f"Unknown evaluation agent: {agent}")
            state.step(int(action))
            state.auto_step(self.rust_db)

        winner = int(state.get_winner()) if state.is_terminal() else -1
        state_json = json.loads(state.to_json())
        return {
            "winner": winner,
            "turn": int(state.turn),
            "p0_score": int(state_json["players"][0]["score"]),
            "p1_score": int(state_json["players"][1]["score"]),
            "p0_lives": len(state_json["players"][0].get("success_lives", [])),
            "p1_lives": len(state_json["players"][1].get("success_lives", [])),
        }

    def benchmark_matchup(self, opponent: str, games: int | None = None, seed_base: int | None = None) -> dict[str, float | int]:
        total_games = int(games or self.config.benchmark_games)
        total_games = max(2, total_games)
        pair_count = max(1, total_games // 2)
        base_seed = int(seed_base if seed_base is not None else self.config.benchmark_seed_base)
        model_search_sims = self._effective_benchmark_model_search_sims()
        opponent_search_sims = self._effective_benchmark_search_sims() if opponent == "search" else model_search_sims
        results: list[dict[str, float | int]] = []
        start = time.perf_counter()
        for pair_idx in range(pair_count):
            seed = base_seed + pair_idx
            forward = self._play_match(
                seed,
                "model",
                opponent,
                model_search_sims=model_search_sims,
                opponent_search_sims=opponent_search_sims,
            )
            reverse = self._play_match(
                seed,
                opponent,
                "model",
                model_search_sims=model_search_sims,
                opponent_search_sims=opponent_search_sims,
            )
            results.append(forward)
            reverse_winner = int(reverse["winner"])
            if reverse_winner == 0:
                reverse_result = 1
            elif reverse_winner == 1:
                reverse_result = 0
            else:
                reverse_result = -1
            results.append(
                {
                    "winner": reverse_result,
                    "turn": int(reverse["turn"]),
                    "p0_score": int(reverse["p1_score"]),
                    "p1_score": int(reverse["p0_score"]),
                    "p0_lives": int(reverse["p1_lives"]),
                    "p1_lives": int(reverse["p0_lives"]),
                }
            )

        rows = results[:total_games]
        elapsed = time.perf_counter() - start
        live_margins = [float(row["p0_lives"]) - float(row["p1_lives"]) for row in rows]
        score_margins = [float(row["p0_score"]) - float(row["p1_score"]) for row in rows]
        decisive_rows = [row for row in rows if int(row["winner"]) != -1]
        turn_values = [float(row["turn"]) for row in rows]
        return {
            "games": len(rows),
            "model_wins": sum(1 for row in rows if int(row["winner"]) == 0),
            "opponent_wins": sum(1 for row in rows if int(row["winner"]) == 1),
            "draws": sum(1 for row in rows if int(row["winner"]) == -1),
            "avg_turns": float(np.mean(turn_values)) if rows else 0.0,
            "min_turns": float(min(turn_values)) if rows else 0.0,
            "max_turns": float(max(turn_values)) if rows else 0.0,
            "avg_model_score": float(np.mean([float(row["p0_score"]) for row in rows])) if rows else 0.0,
            "avg_opponent_score": float(np.mean([float(row["p1_score"]) for row in rows])) if rows else 0.0,
            "avg_model_lives": float(np.mean([float(row["p0_lives"]) for row in rows])) if rows else 0.0,
            "avg_opponent_lives": float(np.mean([float(row["p1_lives"]) for row in rows])) if rows else 0.0,
            "avg_live_margin": float(np.mean(live_margins)) if rows else 0.0,
            "avg_score_margin": float(np.mean(score_margins)) if rows else 0.0,
            "avg_abs_live_margin": float(np.mean(np.abs(live_margins))) if rows else 0.0,
            "avg_abs_score_margin": float(np.mean(np.abs(score_margins))) if rows else 0.0,
            "one_live_margin_rate": float(
                sum(1 for row in decisive_rows if abs(int(row["p0_lives"]) - int(row["p1_lives"])) <= 1)
                / max(1, len(decisive_rows))
            ),
            "one_score_margin_rate": float(
                sum(1 for row in decisive_rows if abs(int(row["p0_score"]) - int(row["p1_score"])) <= 1)
                / max(1, len(decisive_rows))
            ),
            "model_agent": "neural_mcts" if self._uses_neural_mcts_targets() else "policy",
            "opponent_agent": opponent,
            "model_search_sims": int(model_search_sims if self._uses_neural_mcts_targets() else 0),
            "opponent_search_sims": int(opponent_search_sims if opponent in {"search", "reference"} else 0),
            "elapsed_sec": elapsed,
            "sec_per_game": float(elapsed / max(1, len(rows))),
            "games_per_sec": float(len(rows) / max(elapsed, 1e-9)),
        }

    def benchmark_suite(self, games: int | None = None, seed_base: int | None = None) -> dict[str, dict[str, float | int]]:
        start = time.perf_counter()
        base_seed = int(seed_base if seed_base is not None else self.config.benchmark_seed_base)
        greedy = self.benchmark_matchup("greedy", games=games, seed_base=base_seed)
        search = self.benchmark_matchup("search", games=games, seed_base=base_seed + 50_000)
        suite = {"vs_greedy": greedy, "vs_search": search}
        if self.config.turnseq_benchmark_games > 0:
            suite["vs_turnseq"] = self.benchmark_matchup(
                "turnseq",
                games=self.config.turnseq_benchmark_games,
                seed_base=base_seed + 100_000,
            )
        if self.reference_model is not None and self.config.reference_benchmark_games > 0:
            suite["vs_reference"] = self.benchmark_matchup(
                "reference",
                games=self.config.reference_benchmark_games,
                seed_base=base_seed + 150_000,
            )
        suite["summary"] = {"elapsed_sec": time.perf_counter() - start}
        return suite

    def _fixed_seed_setup_hash(self, seed: int) -> str:
        state = self._new_state(seed)
        _apply_deterministic_setup(state, self.rust_db)
        payload = json.dumps(json.loads(state.to_json()), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _collect_fixed_seed_trace(self, seed: int) -> list[PositionRecord]:
        state = self._new_state(seed)
        _apply_deterministic_setup(state, self.rust_db)
        pending: list[dict[str, object]] = []

        while not state.is_terminal() and int(state.turn) < self.config.max_turns:
            legal_ids = [int(action_id) for action_id in state.get_legal_action_ids()]
            if not legal_ids:
                state.auto_step(self.rust_db)
                continue

            phase = int(state.phase)
            if phase in (PHASE_RPS, PHASE_TURN_ORDER):
                state.step(int(min(legal_ids)))
                state.auto_step(self.rust_db)
                continue

            legal_mask, legal_policy_ids, mapping = build_legal_policy_context(legal_ids, self.initial_deck, phase)
            if len(legal_policy_ids) == 0:
                state.step(int(legal_ids[0]))
                state.auto_step(self.rust_db)
                continue

            obs = build_state_observation(state, self.config.observation_mode)
            suggestions = state.get_mcts_suggestions(self.config.search_sims)
            target_policy = self._policy_target_from_suggestions(state, phase, legal_mask, suggestions)
            if target_policy.sum() <= 0:
                chosen_policy_id = int(legal_policy_ids[0])
                target_policy = self._one_hot_policy(chosen_policy_id)
            else:
                chosen_policy_id = self._argmax_policy_action(target_policy, legal_policy_ids)

            pending.append(
                {
                    "obs": obs,
                    "policy": target_policy,
                    "legal_policy_ids": legal_policy_ids.astype(np.int32),
                    "player": int(state.current_player),
                }
            )

            action = int(mapping.get(chosen_policy_id, legal_ids[0]))
            state.step(action)
            state.auto_step(self.rust_db)

        winner = int(state.get_winner()) if state.is_terminal() else -1
        records: list[PositionRecord] = []
        for entry in pending:
            player = int(entry["player"])
            value_target = 0.0 if winner == -1 else (1.0 if winner == player else -1.0)
            records.append(
                PositionRecord(
                    obs=np.asarray(entry["obs"], dtype=np.float32),
                    policy=np.asarray(entry["policy"], dtype=np.float32),
                    legal_policy_ids=np.asarray(entry["legal_policy_ids"], dtype=np.int32),
                    value_target=float(value_target),
                )
            )
        return records

    def evaluate_fixed_seed_alignment(self, seed: int) -> dict[str, float]:
        records = self._collect_fixed_seed_trace(seed)
        if not records:
            return {
                "positions": 0.0,
                "policy_ce": 0.0,
                "top1_acc": 0.0,
                "value_mse": 0.0,
                "value_sign_acc": 0.0,
                "winning_value_mean": 0.0,
                "losing_value_mean": 0.0,
            }
        metrics = evaluate_records(self.model, records, self.device)
        metrics["positions"] = float(len(records))
        return metrics

    def evaluate_fixed_seed_rollout(self, seed: int, action_source: str) -> dict[str, float | int | str]:
        result = self.play_self_play_game(
            seed,
            action_source_override=action_source,
            training_target_mode_override="search",
        )
        reward = self._game_reward_breakdown(result)
        return {
            "action_source": str(action_source),
            "winner": int(result.winner),
            "turns": int(result.turns),
            "reward": float(reward.reward),
            "fast_win": float(int(reward.is_fast_win)),
            "p0_score": int(result.p0_score),
            "p1_score": int(result.p1_score),
            "p0_lives": int(result.p0_lives),
            "p1_lives": int(result.p1_lives),
            "teacher_match_rate": float(result.chosen_teacher_match_actions / max(1, result.decisions)),
            "model_teacher_match_rate": float(result.model_teacher_match_actions / max(1, result.model_eval_actions)),
        }

    def play_self_play_game(
        self,
        seed: int,
        action_source_override: str | None = None,
        training_target_mode_override: str | None = None,
    ) -> SelfPlayGameResult:
        rng = random.Random(seed)
        state = self._new_state(seed)
        _apply_deterministic_setup(state, self.rust_db)
        records: list[dict[str, object]] = []
        teacher_action_prob = self._teacher_action_probability()
        effective_training_target_mode = str(training_target_mode_override or self.config.training_target_mode).lower()
        use_search_targets = effective_training_target_mode == "search"
        use_neural_mcts_targets = effective_training_target_mode == "neural_mcts"
        decision_count = 0
        model_eval_actions = 0
        contested_pass_actions = 0
        teacher_forced_actions = 0
        chosen_teacher_match_actions = 0
        model_teacher_match_actions = 0
        game_start = time.perf_counter()
        model_infer_sec = 0.0
        teacher_search_sec = 0.0
        env_step_sec = 0.0
        action_source = str(action_source_override or self.config.selfplay_action_source).lower()

        while not state.is_terminal() and int(state.turn) < self.config.max_turns:
            legal_ids = [int(action_id) for action_id in state.get_legal_action_ids()]
            if not legal_ids:
                step_start = time.perf_counter()
                state.auto_step(self.rust_db)
                env_step_sec += time.perf_counter() - step_start
                continue

            phase = int(state.phase)
            legal_mask, legal_policy_ids, mapping = build_legal_policy_context(legal_ids, self.initial_deck, phase)
            if len(legal_policy_ids) == 0:
                step_start = time.perf_counter()
                state.step(int(legal_ids[0]))
                state.auto_step(self.rust_db)
                env_step_sec += time.perf_counter() - step_start
                continue

            if len(legal_policy_ids) == 1:
                only_policy_id = int(legal_policy_ids[0])
                engine_action = int(mapping.get(only_policy_id, legal_ids[0]))
                decision_count += 1
                model_eval_actions += 1
                chosen_teacher_match_actions += 1
                model_teacher_match_actions += 1
                records.append(
                    {
                        "obs": build_state_observation(state, self.config.observation_mode),
                        "policy": self._one_hot_policy(only_policy_id),
                        "legal_policy_ids": legal_policy_ids.astype(np.int32),
                        "player": int(state.current_player),
                        "turn": int(state.turn),
                        "contested_pass": False,
                        "immediate_live_gain": 0.0,
                        "immediate_score_gain": 0.0,
                        "setup_progress_gain": 0.0,
                        "coverage_gain": 0.0,
                        "live_set_gain": 0.0,
                        "max_stage_cost_gain": 0.0,
                    }
                )
                step_start = time.perf_counter()
                state.step(engine_action)
                state.auto_step(self.rust_db)
                env_step_sec += time.perf_counter() - step_start
                continue

            obs = build_state_observation(state, self.config.observation_mode)
            before_state_json = json.loads(state.to_json())
            acting_player = int(state.current_player)
            teacher_forced = False
            target_policy = None
            teacher_top_policy_id = -1
            model_top_policy_id = -1
            probs = None
            chosen_policy_id = None
            if use_neural_mcts_targets:
                search_start = time.perf_counter()
                suggestions = self._search_neural_mcts(state)
                teacher_search_sec += time.perf_counter() - search_start
                target_policy = self._policy_target_from_suggestions(state, phase, legal_mask, suggestions)
                teacher_forced = False
                teacher_top_policy_id = int(legal_policy_ids[np.argmax(target_policy[legal_policy_ids])])
                if action_source in {"model_sample", "model_greedy"}:
                    infer_start = time.perf_counter()
                    probs, _ = self._model_inference(obs, legal_mask)
                    model_infer_sec += time.perf_counter() - infer_start
                    model_top_policy_id = int(legal_policy_ids[np.argmax(probs[legal_policy_ids])])
                    model_eval_actions += 1
                    if action_source == "model_greedy":
                        chosen_policy_id = model_top_policy_id
                    execution_policy = probs
                else:
                    model_top_policy_id = teacher_top_policy_id
                    model_eval_actions += 1
                    execution_policy = target_policy
                    if action_source == "search_greedy":
                        chosen_policy_id = teacher_top_policy_id
            elif use_search_targets:
                search_start = time.perf_counter()
                suggestions = state.get_mcts_suggestions(self.config.search_sims)
                teacher_search_sec += time.perf_counter() - search_start
                target_policy = self._policy_target_from_suggestions(state, phase, legal_mask, suggestions)
                teacher_top_policy_id = int(legal_policy_ids[np.argmax(target_policy[legal_policy_ids])])

                if action_source in {"model_sample", "model_greedy", "hybrid_teacher"}:
                    infer_start = time.perf_counter()
                    probs, _ = self._model_inference(obs, legal_mask)
                    model_infer_sec += time.perf_counter() - infer_start
                    model_top_policy_id = int(legal_policy_ids[np.argmax(probs[legal_policy_ids])])
                    model_eval_actions += 1

                if action_source == "search_sample":
                    teacher_forced = True
                    execution_policy = target_policy
                elif action_source == "search_greedy":
                    teacher_forced = True
                    chosen_policy_id = teacher_top_policy_id
                    execution_policy = target_policy
                elif action_source == "model_sample":
                    execution_policy = probs
                elif action_source == "model_greedy":
                    chosen_policy_id = model_top_policy_id
                    execution_policy = probs
                else:
                    teacher_forced = rng.random() < teacher_action_prob
                    execution_policy = target_policy if teacher_forced else probs
            else:
                infer_start = time.perf_counter()
                probs, _ = self._model_inference(obs, legal_mask)
                model_infer_sec += time.perf_counter() - infer_start
                model_top_policy_id = int(legal_policy_ids[np.argmax(probs[legal_policy_ids])])
                model_eval_actions += 1
                execution_policy = probs

            temperature = self.config.actor_temperature if int(state.turn) <= 4 else max(0.25, self.config.actor_temperature * 0.5)
            epsilon = 0.0 if phase in (PHASE_RPS, PHASE_TURN_ORDER) or use_search_targets else self.config.actor_epsilon
            if chosen_policy_id is None:
                chosen_policy_id = self._choose_policy_action(execution_policy, legal_policy_ids, temperature, epsilon, rng)
            engine_action = int(mapping.get(chosen_policy_id, legal_ids[0]))
            if target_policy is None:
                target_policy = self._one_hot_policy(chosen_policy_id)
                teacher_top_policy_id = chosen_policy_id
            contested_pass = bool(engine_action == ACTION_BASE_PASS and len(legal_ids) > 1)
            decision_count += 1
            contested_pass_actions += int(contested_pass)
            teacher_forced_actions += int(teacher_forced)
            chosen_teacher_match_actions += int(chosen_policy_id == teacher_top_policy_id)
            if model_top_policy_id >= 0:
                model_teacher_match_actions += int(model_top_policy_id == teacher_top_policy_id)

            records.append(
                {
                    "obs": obs,
                    "policy": target_policy,
                    "legal_policy_ids": legal_policy_ids.astype(np.int32),
                    "player": acting_player,
                    "turn": int(state.turn),
                    "contested_pass": contested_pass,
                }
            )
            step_start = time.perf_counter()
            state.step(engine_action)
            state.auto_step(self.rust_db)
            env_step_sec += time.perf_counter() - step_start
            after_state_json = json.loads(state.to_json())
            before_score, before_lives = _player_metrics_from_state_json(before_state_json, acting_player)
            after_score, after_lives = _player_metrics_from_state_json(after_state_json, acting_player)
            progress = self._strategic_progress_delta(before_state_json, after_state_json, acting_player)
            records[-1]["immediate_live_gain"] = float(after_lives - before_lives)
            records[-1]["immediate_score_gain"] = float(after_score - before_score)
            records[-1].update(progress)

        winner = int(state.get_winner()) if state.is_terminal() else -1
        state_json = json.loads(state.to_json())
        final_scores = (
            int(state_json["players"][0]["score"]),
            int(state_json["players"][1]["score"]),
        )
        final_lives = (
            len(state_json["players"][0].get("success_lives", [])),
            len(state_json["players"][1].get("success_lives", [])),
        )
        output: list[PositionRecord] = []
        for record in records:
            output.append(
                PositionRecord(
                    obs=np.asarray(record["obs"], dtype=np.float32),
                    policy=np.asarray(record["policy"], dtype=np.float32),
                    legal_policy_ids=np.asarray(record["legal_policy_ids"], dtype=np.int32),
                    value_target=_compute_shaped_value_target(
                        record,
                        winner,
                        int(state.turn),
                        self.config.max_turns,
                        final_scores,
                        final_lives,
                        self.config.single_seed_fast_turn_threshold,
                    ),
                )
            )
        return SelfPlayGameResult(
            records=output,
            turns=int(state.turn),
            winner=winner,
            decisions=decision_count,
            model_eval_actions=model_eval_actions,
            contested_pass_actions=contested_pass_actions,
            teacher_forced_actions=teacher_forced_actions,
            chosen_teacher_match_actions=chosen_teacher_match_actions,
            model_teacher_match_actions=model_teacher_match_actions,
            elapsed_sec=time.perf_counter() - game_start,
            model_infer_sec=model_infer_sec,
            teacher_search_sec=teacher_search_sec,
            env_step_sec=env_step_sec,
            p0_score=int(state_json["players"][0]["score"]),
            p1_score=int(state_json["players"][1]["score"]),
            p0_lives=len(state_json["players"][0].get("success_lives", [])),
            p1_lives=len(state_json["players"][1].get("success_lives", [])),
        )

    def generate_self_play(self, num_games: int, seed_offset: int = 0) -> dict[str, float]:
        start = time.perf_counter()
        produced = 0
        skipped_draw_games = 0
        skipped_draw_records = 0
        focused_games = 0
        total_reward = 0.0
        min_reward = None
        max_reward = 0.0
        total_turns = 0
        min_turns = None
        max_turns = 0
        decisive_games = 0
        draws = 0
        total_decisions = 0
        total_model_eval_actions = 0
        total_contested_pass_actions = 0
        total_teacher_forced_actions = 0
        total_chosen_teacher_match_actions = 0
        total_model_teacher_match_actions = 0
        total_game_sec = 0.0
        total_model_infer_sec = 0.0
        total_teacher_search_sec = 0.0
        total_env_step_sec = 0.0
        total_abs_live_margin = 0.0
        total_abs_score_margin = 0.0
        one_live_margin_games = 0
        one_score_margin_games = 0
        for game_idx in range(num_games):
            seed, from_focus_bank = self._choose_self_play_seed(game_idx, seed_offset)
            focused_games += int(from_focus_bank)
            game_result = self.play_self_play_game(seed)
            game_reward = self._game_reward_breakdown(game_result).reward
            total_reward += game_reward
            min_reward = game_reward if min_reward is None else min(min_reward, game_reward)
            max_reward = max(max_reward, game_reward)
            total_turns += game_result.turns
            min_turns = game_result.turns if min_turns is None else min(min_turns, game_result.turns)
            max_turns = max(max_turns, game_result.turns)
            decisive_games += int(game_result.winner != -1)
            draws += int(game_result.winner == -1)
            total_decisions += game_result.decisions
            total_model_eval_actions += game_result.model_eval_actions
            total_contested_pass_actions += game_result.contested_pass_actions
            total_teacher_forced_actions += game_result.teacher_forced_actions
            total_chosen_teacher_match_actions += game_result.chosen_teacher_match_actions
            total_model_teacher_match_actions += game_result.model_teacher_match_actions
            total_game_sec += game_result.elapsed_sec
            total_model_infer_sec += game_result.model_infer_sec
            total_teacher_search_sec += game_result.teacher_search_sec
            total_env_step_sec += game_result.env_step_sec
            live_margin = abs(int(game_result.p0_lives) - int(game_result.p1_lives))
            score_margin = abs(int(game_result.p0_score) - int(game_result.p1_score))
            total_abs_live_margin += live_margin
            total_abs_score_margin += score_margin
            if game_result.winner != -1:
                one_live_margin_games += int(live_margin <= 1)
                one_score_margin_games += int(score_margin <= 1)
            if self.config.skip_draw_records and game_result.winner == -1:
                skipped_draw_games += 1
                skipped_draw_records += len(game_result.records)
                continue
            for record in game_result.records:
                self.buffer.add(
                    record.obs,
                    dense_to_sparse(record.policy),
                    np.asarray([record.value_target], dtype=np.float32),
                    record.legal_policy_ids,
                )
                produced += 1
        self.buffer.flush()
        elapsed = time.perf_counter() - start
        return {
            "generated": float(produced),
            "games": float(num_games),
            "focused_games": float(focused_games),
            "avg_reward": float(total_reward / max(1, num_games)),
            "min_reward": float(min_reward or 0.0),
            "max_reward": float(max_reward),
            "skipped_draw_games": float(skipped_draw_games),
            "skipped_draw_records": float(skipped_draw_records),
            "decisive_games": float(decisive_games),
            "draws": float(draws),
            "avg_turns": float(total_turns / max(1, num_games)),
            "min_turns": float(min_turns or 0),
            "max_turns": float(max_turns),
            "avg_positions_per_game": float(produced / max(1, num_games)),
            "avg_abs_live_margin": float(total_abs_live_margin / max(1, num_games)),
            "avg_abs_score_margin": float(total_abs_score_margin / max(1, num_games)),
            "contested_pass_rate": float(total_contested_pass_actions / max(1, total_decisions)),
            "teacher_forced_rate": float(total_teacher_forced_actions / max(1, total_decisions)),
            "model_eval_rate": float(total_model_eval_actions / max(1, total_decisions)),
            "chosen_teacher_match_rate": float(total_chosen_teacher_match_actions / max(1, total_decisions)),
            "model_teacher_match_rate": float(total_model_teacher_match_actions / max(1, total_model_eval_actions)),
            "one_live_margin_rate": float(one_live_margin_games / max(1, decisive_games)),
            "one_score_margin_rate": float(one_score_margin_games / max(1, decisive_games)),
            "selfplay_sec": float(elapsed),
            "avg_game_sec": float(total_game_sec / max(1, num_games)),
            "positions_per_sec": float(produced / max(elapsed, 1e-9)),
            "decisions_per_sec": float(total_decisions / max(elapsed, 1e-9)),
            "model_infer_sec": float(total_model_infer_sec),
            "teacher_search_sec": float(total_teacher_search_sec),
            "env_step_sec": float(total_env_step_sec),
            "focus_seed_bank_size": float(len(self.focus_seed_bank)),
        }

    def train_step(self, batch_size: int) -> dict[str, float]:
        batch = self.buffer.sample(batch_size)
        if batch is None:
            return {"loss": 0.0, "policy_loss": 0.0, "value_loss": 0.0, "policy_acc": 0.0, "batch_rows": 0.0}

        batch_obs, sparse_policy, mask_np, batch_values = batch
        rows = int(batch_obs.shape[0])
        target_policy = np.zeros((rows, ACTION_SPACE), dtype=np.float32)
        row_idx, col_idx, values = sparse_policy
        target_policy[row_idx, col_idx] = values

        obs_t = torch.from_numpy(batch_obs).to(self.device)
        mask_t = torch.from_numpy(mask_np).to(self.device)
        target_policy_t = torch.from_numpy(target_policy).to(self.device)
        value_t = torch.from_numpy(batch_values[:, 0]).to(self.device)

        self.model.train()
        self.optimizer.zero_grad(set_to_none=True)
        with torch.amp.autocast(device_type=self.autocast_device, enabled=self.amp_enabled):
            logits, value_out = self.model(obs_t, mask=mask_t)
            log_probs = torch.log_softmax(logits, dim=1)
            probs = torch.softmax(logits, dim=1)
            policy_loss = -(target_policy_t * log_probs).sum(dim=1).mean()
            entropy = -(probs * log_probs).sum(dim=1).mean()
            value_loss = F.smooth_l1_loss(value_out[:, 0], value_t)
            loss = policy_loss + self.config.value_coef * value_loss - self.config.entropy_coef * entropy

        self.scaler.scale(loss).backward()
        self.scaler.unscale_(self.optimizer)
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.gradient_clip)
        self.scaler.step(self.optimizer)
        self.scaler.update()
        self.model.eval()

        policy_acc = float((probs.argmax(dim=1) == target_policy_t.argmax(dim=1)).float().mean().item())
        return {
            "loss": float(loss.item()),
            "policy_loss": float(policy_loss.item()),
            "value_loss": float(value_loss.item()),
            "policy_acc": policy_acc,
            "batch_rows": float(rows),
        }

    def train_iteration(self) -> dict[str, float]:
        iteration_start = time.perf_counter()
        active_deck = self._activate_iteration_deck()
        active_seed = self._current_single_seed() if self._uses_single_seed_eval() else -1
        selfplay = self.generate_self_play(self.config.games_per_iteration)
        eval_summary = self._evaluate_current_single_seed() if self._uses_single_seed_eval() else None
        eval_reward = float(eval_summary.avg_reward) if eval_summary is not None else -1.0
        eval_decisive_rate = float(eval_summary.decisive_rate) if eval_summary is not None else -1.0
        eval_fast_win_rate = float(eval_summary.fast_win_rate) if eval_summary is not None else -1.0
        eval_avg_turns = float(eval_summary.avg_turns) if eval_summary is not None else -1.0
        seed_certified_now = (
            float(
                int(
                    seed_certified(
                        eval_summary,
                        target_reward=self.config.single_seed_target_reward,
                        target_decisive_rate=self.config.single_seed_target_decisive_rate,
                        target_fast_win_rate=self.config.single_seed_target_fast_win_rate,
                        target_avg_turns=self.config.single_seed_target_avg_turns,
                    )
                )
            )
            if eval_summary is not None
            else 0.0
        )
        if self.buffer.count < self.config.min_buffer_items:
            row = {
                "iteration": float(self.iteration),
                "deck_name": str(active_deck.get("name", "deck")),
                "active_seed": float(active_seed),
                "eval_reward": float(eval_reward),
                "eval_decisive_rate": float(eval_decisive_rate),
                "eval_fast_win_rate": float(eval_fast_win_rate),
                "eval_avg_turns": float(eval_avg_turns),
                "seed_certified": float(seed_certified_now),
                "seed_advanced": 0.0,
                "seed_iteration": float(self.single_seed_iteration_count),
                **selfplay,
                "buffer_count": float(self.buffer.count),
                "train_steps": 0.0,
                "train_samples": 0.0,
                "replay_ratio": 0.0,
                "train_sec": 0.0,
                "train_steps_per_sec": 0.0,
                "train_samples_per_sec": 0.0,
                "avg_loss": 0.0,
                "avg_policy_loss": 0.0,
                "avg_value_loss": 0.0,
                "avg_policy_acc": 0.0,
                "teacher_action_prob": self._teacher_action_probability(),
                "duration_sec": time.perf_counter() - iteration_start,
            }
            if str(self.config.selfplay_seed_mode).lower() == "curriculum_single":
                row["seed_advanced"] = float(int(self._maybe_advance_single_seed(eval_summary, bool(seed_certified_now))))
                row["seed_iteration"] = float(self.single_seed_iteration_count)
            self._append_log_row(row)
            return row

        train_start = time.perf_counter()
        train_steps = int(self.config.training_steps_per_iteration)
        if self.config.target_replay_ratio > 0.0 and self.config.batch_size > 0:
            capped_steps = max(1, int((selfplay["generated"] * self.config.target_replay_ratio) // self.config.batch_size))
            train_steps = min(train_steps, capped_steps)
        metrics = [self.train_step(self.config.batch_size) for _ in range(train_steps)]
        train_sec = time.perf_counter() - train_start
        train_samples = float(sum(entry["batch_rows"] for entry in metrics))
        row = {
            "iteration": float(self.iteration),
            "deck_name": str(active_deck.get("name", "deck")),
            "active_seed": float(active_seed),
            "eval_reward": float(eval_reward),
            "eval_decisive_rate": float(eval_decisive_rate),
            "eval_fast_win_rate": float(eval_fast_win_rate),
            "eval_avg_turns": float(eval_avg_turns),
            "seed_certified": float(seed_certified_now),
            "seed_advanced": 0.0,
            "seed_iteration": float(self.single_seed_iteration_count),
            **selfplay,
            "buffer_count": float(self.buffer.count),
            "train_steps": float(len(metrics)),
            "train_samples": train_samples,
            "replay_ratio": float(train_samples / max(selfplay["generated"], 1.0)),
            "train_sec": float(train_sec),
            "train_steps_per_sec": float(len(metrics) / max(train_sec, 1e-9)),
            "train_samples_per_sec": float(train_samples / max(train_sec, 1e-9)),
            "avg_loss": float(np.mean([entry["loss"] for entry in metrics])),
            "avg_policy_loss": float(np.mean([entry["policy_loss"] for entry in metrics])),
            "avg_value_loss": float(np.mean([entry["value_loss"] for entry in metrics])),
            "avg_policy_acc": float(np.mean([entry["policy_acc"] for entry in metrics])),
            "teacher_action_prob": self._teacher_action_probability(),
            "learning_rate": float(self.optimizer.param_groups[0]["lr"]),
            "duration_sec": time.perf_counter() - iteration_start,
        }
        if str(self.config.selfplay_seed_mode).lower() == "curriculum_single":
            row["seed_advanced"] = float(int(self._maybe_advance_single_seed(eval_summary, bool(seed_certified_now))))
            row["seed_iteration"] = float(self.single_seed_iteration_count)
        self._append_log_row(row)
        if self.iteration % self.config.checkpoint_every == 0:
            self._save_checkpoint(reason="iteration", advance_iteration=True)
        self.iteration += 1
        return row

    def _request_stop(self, signum: int, _frame) -> None:
        self._stop_requested = True
        logger.warning("Received signal %s; will stop after the current safe point and save.", signum)

    def _install_signal_handlers(self) -> dict[int, object]:
        previous: dict[int, object] = {}
        for signum in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)):
            if signum is None:
                continue
            try:
                previous[signum] = signal.getsignal(signum)
                signal.signal(signum, self._request_stop)
            except Exception:
                continue
        return previous

    def _restore_signal_handlers(self, previous: dict[int, object]) -> None:
        for signum, handler in previous.items():
            try:
                signal.signal(signum, handler)
            except Exception:
                continue

    def close(self) -> None:
        if hasattr(self, "buffer") and self.buffer is not None:
            try:
                self.buffer.close()
            except Exception:
                pass

    def run(self) -> None:
        logger.info("Starting vanilla self-play training on %s", self.device)
        logger.info(
            "Observation mode: %s | training=%s | deck_mode: %s | decks=%s | active_deck=%s | seed_mode=%s | focus_bank=%s | active_seed=%s",
            self.config.observation_mode,
            self.config.training_target_mode,
            self.config.deck_rotation_mode,
            len(self.decks),
            self.deck["name"],
            self.config.selfplay_seed_mode,
            len(self.focus_seed_bank),
            self._current_single_seed() if self._uses_single_seed_eval() else -1,
        )
        logger.info(
            "Effective config: model=%s embed=%s batch=%s sims=%s mcts_batch=%s bench_model_sims=%s bench_search_sims=%s replay=%.1fx games=%s steps=%s max_turns=%s buffer=%s benchmark_every=%s",
            self.model_config.preset,
            self.model_config.embed_dim,
            self.config.batch_size,
            self.config.search_sims,
            self.config.neural_mcts_batch_size,
            self._effective_benchmark_model_search_sims(),
            self._effective_benchmark_search_sims(),
            self.config.target_replay_ratio,
            self.config.games_per_iteration,
            self.config.training_steps_per_iteration,
            self.config.max_turns,
            self.config.buffer_size,
            self.config.benchmark_every,
        )
        previous_handlers = self._install_signal_handlers()
        try:
            for _ in range(self.config.num_iterations):
                if self._stop_requested:
                    logger.warning("Stop requested before starting iteration %s; saving and exiting.", self.iteration)
                    self._save_checkpoint(reason="signal_pre_iteration", advance_iteration=False)
                    break
                metrics = self.train_iteration()
                logger.info(
                    "iter=%s deck=%s seed=%s seed_it=%s seed_adv=%s games=%s generated=%s reward=%.3f eval=%.3f eval_decisive=%.3f eval_fast=%.3f eval_turns=%.2f skipped_draw_games=%s replay=%.2fx turns=%.2f[%s,%s] decisive=%s draws=%s live_margin=%.2f score_margin=%.2f pass_alt=%.3f selfplay=%.2fs mcts=%.2fs train=%.2fs/%ssteps buffer=%s lr=%.6f loss=%.4f policy=%.4f value=%.4f policy_acc=%.3f dur=%.2fs",
                    int(metrics["iteration"]),
                    str(metrics.get("deck_name", "deck")),
                    int(metrics.get("active_seed", -1.0)),
                    int(metrics.get("seed_iteration", 0.0)),
                    int(metrics.get("seed_advanced", 0.0)),
                    int(metrics.get("games", 0.0)),
                    int(metrics["generated"]),
                    metrics.get("avg_reward", 0.0),
                    metrics.get("eval_reward", -1.0),
                    metrics.get("eval_decisive_rate", -1.0),
                    metrics.get("eval_fast_win_rate", -1.0),
                    metrics.get("eval_avg_turns", -1.0),
                    int(metrics.get("skipped_draw_games", 0.0)),
                    metrics.get("replay_ratio", 0.0),
                    metrics.get("avg_turns", 0.0),
                    int(metrics.get("min_turns", 0.0)),
                    int(metrics.get("max_turns", 0.0)),
                    int(metrics.get("decisive_games", 0.0)),
                    int(metrics.get("draws", 0.0)),
                    metrics.get("avg_abs_live_margin", 0.0),
                    metrics.get("avg_abs_score_margin", 0.0),
                    metrics.get("contested_pass_rate", 0.0),
                    metrics.get("selfplay_sec", 0.0),
                    metrics.get("teacher_search_sec", 0.0),
                    metrics.get("train_sec", 0.0),
                    int(metrics.get("train_steps", 0.0)),
                    int(metrics["buffer_count"]),
                    metrics.get("learning_rate", 0.0),
                    metrics["avg_loss"],
                    metrics.get("avg_policy_loss", 0.0),
                    metrics.get("avg_value_loss", 0.0),
                    metrics["avg_policy_acc"],
                    metrics["duration_sec"],
                )
                next_iteration = int(self.iteration)
                if self.config.benchmark_every > 0 and next_iteration % self.config.benchmark_every == 0:
                    suite = self.benchmark_suite()
                    benchmark_row = {
                        "iteration": next_iteration,
                        "deck_name": str(self.deck.get("name", "deck")),
                        "benchmark_elapsed_sec": suite["summary"]["elapsed_sec"],
                        "greedy_wins": suite["vs_greedy"]["model_wins"],
                        "greedy_losses": suite["vs_greedy"]["opponent_wins"],
                        "greedy_draws": suite["vs_greedy"]["draws"],
                        "greedy_elapsed_sec": suite["vs_greedy"]["elapsed_sec"],
                        "search_wins": suite["vs_search"]["model_wins"],
                        "search_losses": suite["vs_search"]["opponent_wins"],
                        "search_draws": suite["vs_search"]["draws"],
                        "search_elapsed_sec": suite["vs_search"]["elapsed_sec"],
                        "greedy_avg_turns": suite["vs_greedy"]["avg_turns"],
                        "greedy_min_turns": suite["vs_greedy"]["min_turns"],
                        "greedy_max_turns": suite["vs_greedy"]["max_turns"],
                        "search_avg_turns": suite["vs_search"]["avg_turns"],
                        "search_min_turns": suite["vs_search"]["min_turns"],
                        "search_max_turns": suite["vs_search"]["max_turns"],
                        "greedy_avg_abs_live_margin": suite["vs_greedy"]["avg_abs_live_margin"],
                        "greedy_avg_abs_score_margin": suite["vs_greedy"]["avg_abs_score_margin"],
                        "search_avg_abs_live_margin": suite["vs_search"]["avg_abs_live_margin"],
                        "search_avg_abs_score_margin": suite["vs_search"]["avg_abs_score_margin"],
                    }
                    if "vs_turnseq" in suite:
                        benchmark_row.update(
                            {
                                "turnseq_wins": suite["vs_turnseq"]["model_wins"],
                                "turnseq_losses": suite["vs_turnseq"]["opponent_wins"],
                                "turnseq_draws": suite["vs_turnseq"]["draws"],
                                "turnseq_elapsed_sec": suite["vs_turnseq"]["elapsed_sec"],
                                "turnseq_avg_turns": suite["vs_turnseq"]["avg_turns"],
                                "turnseq_min_turns": suite["vs_turnseq"]["min_turns"],
                                "turnseq_max_turns": suite["vs_turnseq"]["max_turns"],
                            }
                        )
                    if "vs_reference" in suite:
                        benchmark_row.update(
                            {
                                "reference_wins": suite["vs_reference"]["model_wins"],
                                "reference_losses": suite["vs_reference"]["opponent_wins"],
                                "reference_draws": suite["vs_reference"]["draws"],
                                "reference_elapsed_sec": suite["vs_reference"]["elapsed_sec"],
                                "reference_avg_turns": suite["vs_reference"]["avg_turns"],
                                "reference_min_turns": suite["vs_reference"]["min_turns"],
                                "reference_max_turns": suite["vs_reference"]["max_turns"],
                                "reference_avg_abs_live_margin": suite["vs_reference"]["avg_abs_live_margin"],
                                "reference_avg_abs_score_margin": suite["vs_reference"]["avg_abs_score_margin"],
                            }
                        )
                    self._append_benchmark_row(benchmark_row)
                    logger.info(
                        "benchmark iter=%s sec=%.2f greedy=%s-%s-%s(turns=%.2f[%s,%s], live=%.2f, score=%.2f) search=%s-%s-%s(turns=%.2f[%s,%s], live=%.2f, score=%.2f)%s%s",
                        next_iteration,
                        suite["summary"]["elapsed_sec"],
                        suite["vs_greedy"]["model_wins"],
                        suite["vs_greedy"]["opponent_wins"],
                        suite["vs_greedy"]["draws"],
                        suite["vs_greedy"]["avg_turns"],
                        int(suite["vs_greedy"]["min_turns"]),
                        int(suite["vs_greedy"]["max_turns"]),
                        suite["vs_greedy"]["avg_abs_live_margin"],
                        suite["vs_greedy"]["avg_abs_score_margin"],
                        suite["vs_search"]["model_wins"],
                        suite["vs_search"]["opponent_wins"],
                        suite["vs_search"]["draws"],
                        suite["vs_search"]["avg_turns"],
                        int(suite["vs_search"]["min_turns"]),
                        int(suite["vs_search"]["max_turns"]),
                        suite["vs_search"]["avg_abs_live_margin"],
                        suite["vs_search"]["avg_abs_score_margin"],
                        (
                            " turnseq=%s-%s-%s(turns=%.2f[%s,%s], live=%.2f, score=%.2f)"
                            % (
                                suite["vs_turnseq"]["model_wins"],
                                suite["vs_turnseq"]["opponent_wins"],
                                suite["vs_turnseq"]["draws"],
                                suite["vs_turnseq"]["avg_turns"],
                                int(suite["vs_turnseq"]["min_turns"]),
                                int(suite["vs_turnseq"]["max_turns"]),
                                suite["vs_turnseq"]["avg_abs_live_margin"],
                                suite["vs_turnseq"]["avg_abs_score_margin"],
                            )
                            if "vs_turnseq" in suite
                            else ""
                        ),
                        (
                            " ref=%s-%s-%s(turns=%.2f[%s,%s], live=%.2f, score=%.2f)"
                            % (
                                suite["vs_reference"]["model_wins"],
                                suite["vs_reference"]["opponent_wins"],
                                suite["vs_reference"]["draws"],
                                suite["vs_reference"]["avg_turns"],
                                int(suite["vs_reference"]["min_turns"]),
                                int(suite["vs_reference"]["max_turns"]),
                                suite["vs_reference"]["avg_abs_live_margin"],
                                suite["vs_reference"]["avg_abs_score_margin"],
                            )
                            if "vs_reference" in suite
                            else ""
                        ),
                    )
                    logger.debug("benchmark=%s", json.dumps(_rounded(suite)))
                    self._maybe_promote_or_rollback(suite)
                if self._stop_requested:
                    logger.warning("Stop requested after iteration %s; saving and exiting.", int(metrics["iteration"]))
                    self._save_checkpoint(reason="signal_post_iteration", advance_iteration=False)
                    break
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt received; flushing buffer and saving checkpoint before exit.")
            self._save_checkpoint(reason="keyboard_interrupt", advance_iteration=False)
        finally:
            self._restore_signal_handlers(previous_handlers)
            self.close()


def _dataset_to_tensors(records: Sequence[PositionRecord]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    obs = np.stack([record.obs for record in records], axis=0).astype(np.float32)
    policy = np.stack([record.policy for record in records], axis=0).astype(np.float32)
    mask = np.zeros((len(records), ACTION_SPACE), dtype=np.bool_)
    value = np.asarray([record.value_target for record in records], dtype=np.float32)
    for row_idx, record in enumerate(records):
        mask[row_idx, record.legal_policy_ids] = True
    return obs, policy, mask, value


def evaluate_records(model: nn.Module, records: Sequence[PositionRecord], device: torch.device) -> dict[str, float]:
    obs, policy, mask, value = _dataset_to_tensors(records)
    obs_t = torch.from_numpy(obs).to(device)
    policy_t = torch.from_numpy(policy).to(device)
    mask_t = torch.from_numpy(mask).to(device)
    value_t = torch.from_numpy(value).to(device)
    with torch.inference_mode():
        logits, value_out = model(obs_t, mask=mask_t)
        probs = torch.softmax(logits, dim=1)
        log_probs = torch.log_softmax(logits, dim=1)
        pred_value = value_out[:, 0]

    policy_ce = float((-(policy_t * log_probs).sum(dim=1).mean()).item())
    top1_acc = float((probs.argmax(dim=1) == policy_t.argmax(dim=1)).float().mean().item())
    value_mse = float(F.mse_loss(pred_value, value_t).item())
    non_draw = torch.abs(value_t) > 0.5
    sign_acc = float(((pred_value[non_draw] > 0) == (value_t[non_draw] > 0)).float().mean().item()) if bool(non_draw.any()) else 0.0
    winning_mean = float(pred_value[value_t > 0.5].mean().item()) if bool((value_t > 0.5).any()) else 0.0
    losing_mean = float(pred_value[value_t < -0.5].mean().item()) if bool((value_t < -0.5).any()) else 0.0
    return {
        "policy_ce": policy_ce,
        "top1_acc": top1_acc,
        "value_mse": value_mse,
        "value_sign_acc": sign_acc,
        "winning_value_mean": winning_mean,
        "losing_value_mean": losing_mean,
    }


def _clone_state(state: engine_rust.PyGameState, rust_db: engine_rust.PyCardDatabase) -> engine_rust.PyGameState:
    clone = state.copy()
    clone.silent = True
    clone.debug_mode = False
    return clone


def greedy_rollout_value(
    trainer: VanillaSelfPlayTrainer,
    state: engine_rust.PyGameState,
    perspective_player: int,
    turn_limit: int,
) -> float:
    sim = _clone_state(state, trainer.rust_db)
    while not sim.is_terminal() and int(sim.turn) < turn_limit:
        legal_ids = [int(action_id) for action_id in sim.get_legal_action_ids()]
        if not legal_ids:
            sim.auto_step(trainer.rust_db)
            continue
        player = int(sim.current_player)
        try:
            action = int(sim.get_greedy_action(trainer.rust_db, player, 0, None))
        except Exception:
            action = int(legal_ids[0])
        if action not in legal_ids:
            action = int(legal_ids[0])
        sim.step(action)
        sim.auto_step(trainer.rust_db)
    if not sim.is_terminal():
        return 0.0
    winner = int(sim.get_winner())
    if winner == -1:
        return 0.0
    return 1.0 if winner == perspective_player else -1.0


def collect_probe_dataset(
    trainer: VanillaSelfPlayTrainer,
    positions: int,
    seed_base: int,
    positions_per_game: int = 2,
) -> list[PositionRecord]:
    dataset: list[PositionRecord] = []
    game_index = 0
    while len(dataset) < positions:
        seed = seed_base + game_index
        rng = random.Random(seed)
        state = trainer._new_state(seed)
        _apply_deterministic_setup(state, trainer.rust_db)
        captured = 0

        while (
            captured < positions_per_game
            and len(dataset) < positions
            and not state.is_terminal()
            and int(state.turn) < max(4, trainer.config.max_turns)
        ):
            legal_ids = [int(action_id) for action_id in state.get_legal_action_ids()]
            if not legal_ids:
                state.auto_step(trainer.rust_db)
                continue
            int(state.current_player)
            phase = int(state.phase)
            if phase in (PHASE_RPS, PHASE_TURN_ORDER):
                state.step(min(legal_ids))
                state.auto_step(trainer.rust_db)
                continue

            legal_mask, legal_policy_ids, _mapping = build_legal_policy_context(legal_ids, trainer.initial_deck, phase)
            if len(legal_policy_ids) == 0:
                state.step(int(legal_ids[0]))
                state.auto_step(trainer.rust_db)
                continue
            if len(legal_policy_ids) < 2:
                state.step(int(legal_ids[0]))
                state.auto_step(trainer.rust_db)
                continue

            suggestions = state.get_mcts_suggestions(trainer.config.search_sims)
            target_policy = _policy_from_suggestions({}, suggestions, trainer.initial_deck, phase, legal_mask)
            obs = build_state_observation(state, trainer.config.observation_mode)
            best_score = float(suggestions[0][1]) if suggestions else 0.5
            value_target = float((best_score - 0.5) * 2.0)
            dataset.append(
                PositionRecord(
                    obs=obs,
                    policy=target_policy,
                    legal_policy_ids=legal_policy_ids.astype(np.int32),
                    value_target=value_target,
                )
            )
            captured += 1

            if suggestions:
                action = int(suggestions[0][0])
            else:
                action = int(rng.choice(legal_ids))
            state.step(action)
            state.auto_step(trainer.rust_db)

        game_index += 1
    return dataset


def collect_search_dataset(
    trainer: VanillaSelfPlayTrainer,
    num_games: int,
    seed_base: int,
    actor: str = "random",
) -> list[PositionRecord]:
    dataset: list[PositionRecord] = []
    for game_idx in range(num_games):
        seed = seed_base + game_idx
        rng = random.Random(seed)
        state = trainer._new_state(seed)
        pending: list[dict[str, object]] = []

        while not state.is_terminal() and int(state.turn) < trainer.config.max_turns:
            legal_ids = [int(action_id) for action_id in state.get_legal_action_ids()]
            if not legal_ids:
                state.auto_step(trainer.rust_db)
                continue
            current_player = int(state.current_player)
            phase = int(state.phase)
            legal_mask, legal_policy_ids, mapping = build_legal_policy_context(legal_ids, trainer.initial_deck, phase)
            if len(legal_policy_ids) == 0:
                state.step(int(legal_ids[0]))
                state.auto_step(trainer.rust_db)
                continue

            suggestions = state.get_mcts_suggestions(trainer.config.search_sims)
            target_policy = _policy_from_suggestions({}, suggestions, trainer.initial_deck, phase, legal_mask)
            obs = build_state_observation(state, trainer.config.observation_mode)
            pending.append(
                {
                    "obs": obs,
                    "policy": target_policy,
                    "legal_policy_ids": legal_policy_ids.astype(np.int32),
                    "player": current_player,
                }
            )

            if actor == "search" and suggestions:
                action = int(suggestions[0][0])
            elif actor == "model":
                probs, _ = trainer._model_inference(obs, legal_mask)
                chosen = trainer._choose_policy_action(probs, legal_policy_ids, 0.35, 0.0, rng)
                action = int(mapping.get(chosen, legal_ids[0]))
            else:
                action = int(rng.choice(legal_ids))
            state.step(action)
            state.auto_step(trainer.rust_db)

        winner = int(state.get_winner()) if state.is_terminal() else -1
        for entry in pending:
            player = int(entry["player"])
            value_target = 0.0 if winner == -1 else (1.0 if winner == player else -1.0)
            dataset.append(
                PositionRecord(
                    obs=np.asarray(entry["obs"], dtype=np.float32),
                    policy=np.asarray(entry["policy"], dtype=np.float32),
                    legal_policy_ids=np.asarray(entry["legal_policy_ids"], dtype=np.int32),
                    value_target=value_target,
                )
            )
    return dataset


def overfit_dataset(
    model: nn.Module,
    optimizer: optim.Optimizer,
    records: Sequence[PositionRecord],
    device: torch.device,
    steps: int,
    batch_size: int,
    amp_enabled: bool,
) -> None:
    obs, policy, mask, value = _dataset_to_tensors(records)
    scaler = torch.amp.GradScaler("cuda", enabled=amp_enabled)
    rng = np.random.default_rng(2026)
    for _ in range(steps):
        indices = rng.choice(len(records), size=min(batch_size, len(records)), replace=len(records) < batch_size)
        obs_t = torch.from_numpy(obs[indices]).to(device)
        policy_t = torch.from_numpy(policy[indices]).to(device)
        mask_t = torch.from_numpy(mask[indices]).to(device)
        value_t = torch.from_numpy(value[indices]).to(device)
        optimizer.zero_grad(set_to_none=True)
        with torch.amp.autocast(device_type=device.type if device.type in {"cuda", "cpu"} else "cpu", enabled=amp_enabled):
            logits, value_out = model(obs_t, mask=mask_t)
            log_probs = torch.log_softmax(logits, dim=1)
            probs = torch.softmax(logits, dim=1)
            policy_loss = -(policy_t * log_probs).sum(dim=1).mean()
            value_loss = F.smooth_l1_loss(value_out[:, 0], value_t)
            entropy = -(probs * log_probs).sum(dim=1).mean()
            loss = policy_loss + 0.5 * value_loss - 0.001 * entropy
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(optimizer)
        scaler.update()


def run_smoke(config: OvernightConfig) -> dict[str, float]:
    trainer = VanillaSelfPlayTrainer(config)
    try:
        generated = trainer.generate_self_play(num_games=1)
        metrics = trainer.train_step(batch_size=min(config.batch_size, max(trainer.buffer.count, 1)))
        summary = {**generated, "buffer_count": float(trainer.buffer.count), **metrics}
        logger.info("Smoke summary: %s", _rounded(summary))
        return summary
    finally:
        trainer.close()


def run_learning_proof(config: OvernightConfig) -> dict[str, dict[str, float]]:
    trainer = VanillaSelfPlayTrainer(config)
    try:
        dataset = collect_probe_dataset(
            trainer,
            positions=max(12, config.proof_games * 4),
            seed_base=config.seed + 50_000,
            positions_per_game=2,
        )
        if len(dataset) < 12:
            raise RuntimeError(f"Proof dataset too small: {len(dataset)} positions")

        split = max(8, int(len(dataset) * 0.75))
        train_records = dataset[:split]
        holdout_records = dataset[split:]

        trained_model = VanillaPolicyModel(config=trainer.model_config).to(trainer.device)
        optimizer = optim.AdamW(trained_model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)

        before_train = evaluate_records(trained_model, train_records, trainer.device)
        before_holdout = evaluate_records(trained_model, holdout_records, trainer.device)
        overfit_dataset(
            trained_model,
            optimizer,
            train_records,
            trainer.device,
            steps=config.proof_train_steps,
            batch_size=min(config.batch_size, len(train_records)),
            amp_enabled=trainer.amp_enabled,
        )
        after_train = evaluate_records(trained_model, train_records, trainer.device)
        after_holdout = evaluate_records(trained_model, holdout_records, trainer.device)

        proof = {
            "dataset": {
                "positions": float(len(dataset)),
                "train_positions": float(len(train_records)),
                "holdout_positions": float(len(holdout_records)),
            },
            "before_train": before_train,
            "after_train": after_train,
            "before_holdout": before_holdout,
            "after_holdout": after_holdout,
        }
        logger.info("Learning proof: %s", json.dumps(_rounded(proof), indent=2))
        return proof
    finally:
        trainer.close()


def run_benchmark(config: OvernightConfig) -> dict[str, dict[str, float | int]]:
    trainer = VanillaSelfPlayTrainer(config)
    try:
        suite = trainer.benchmark_suite(games=config.benchmark_games, seed_base=config.benchmark_seed_base)
        logger.info("Benchmark summary: %s", json.dumps(_rounded(suite), indent=2))
        return suite
    finally:
        trainer.close()


def run_certify(config: OvernightConfig, games: int | None = None) -> dict[str, object]:
    trainer = VanillaSelfPlayTrainer(config)
    try:
        seed = trainer._current_single_seed()
        total_games = max(1, int(games or config.curriculum_eval_games))
        rows: list[dict[str, int | float]] = []
        samples: list[dict[str, object]] = []
        for _ in range(total_games):
            result = trainer.play_self_play_game(seed)
            breakdown = trainer._game_reward_breakdown(result)
            rows.append(
                {
                    "winner": int(result.winner),
                    "turns": int(result.turns),
                    "p0_score": int(result.p0_score),
                    "p1_score": int(result.p1_score),
                    "p0_lives": int(result.p0_lives),
                    "p1_lives": int(result.p1_lives),
                }
            )
            if len(samples) < 8:
                samples.append(
                    {
                        "winner": int(result.winner),
                        "turns": int(result.turns),
                        "p0_score": int(result.p0_score),
                        "p1_score": int(result.p1_score),
                        "p0_lives": int(result.p0_lives),
                        "p1_lives": int(result.p1_lives),
                        "reward": float(breakdown.reward),
                        "speed_bonus": float(breakdown.speed_bonus),
                        "live_margin_bonus": float(breakdown.live_margin_bonus),
                        "score_margin_bonus": float(breakdown.score_margin_bonus),
                        "is_fast_win": bool(breakdown.is_fast_win),
                    }
                )
        summary = summarize_seed_certification(
            rows,
            max_turns=int(config.max_turns),
            fast_win_turn_threshold=int(config.single_seed_fast_turn_threshold),
        )
        report = {
            "seed": int(seed),
            "games": int(total_games),
            "summary": _rounded(asdict(summary)),
            "certified": bool(
                seed_certified(
                    summary,
                    target_reward=config.single_seed_target_reward,
                    target_decisive_rate=config.single_seed_target_decisive_rate,
                    target_fast_win_rate=config.single_seed_target_fast_win_rate,
                    target_avg_turns=config.single_seed_target_avg_turns,
                )
            ),
            "thresholds": {
                "target_reward": float(config.single_seed_target_reward),
                "target_decisive_rate": float(config.single_seed_target_decisive_rate),
                "target_fast_win_rate": float(config.single_seed_target_fast_win_rate),
                "target_avg_turns": float(config.single_seed_target_avg_turns),
                "fast_win_turn_threshold": int(config.single_seed_fast_turn_threshold),
            },
            "samples": samples,
        }
        logger.info("Reward certification: %s", json.dumps(_rounded(report), indent=2))
        return report
    finally:
        trainer.close()


def run_single_seed_proof(config: OvernightConfig) -> dict[str, object]:
    proof_config = copy.deepcopy(config)
    proof_config.selfplay_seed_mode = "curriculum_single"
    proof_config.curriculum_eval_games = max(1, int(config.proof_eval_games))
    trainer = VanillaSelfPlayTrainer(proof_config)
    seed = trainer._current_single_seed()

    logger.info(
        "Starting single-seed proof: seed=%s iterations=%s games=%s steps=%s sims=%s batch=%s device=%s output_csv=%s",
        int(seed),
        int(proof_config.num_iterations),
        int(proof_config.games_per_iteration),
        int(proof_config.training_steps_per_iteration),
        int(proof_config.search_sims),
        int(proof_config.batch_size),
        str(proof_config.device),
        str(proof_config.proof_log_csv),
    )

    setup_hashes = [trainer._fixed_seed_setup_hash(seed) for _ in range(max(2, int(proof_config.proof_eval_games)))]
    deterministic_setup = len(set(setup_hashes)) == 1

    rows: list[dict[str, object]] = []

    def _capture_row(train_metrics: dict[str, float] | None) -> dict[str, object]:
        alignment = trainer.evaluate_fixed_seed_alignment(seed)
        search_rollout = trainer.evaluate_fixed_seed_rollout(seed, "search_greedy")
        model_rollout = trainer.evaluate_fixed_seed_rollout(seed, "model_greedy")
        row = {
            "iteration": int(trainer.iteration),
            "seed": int(seed),
            "setup_hash": setup_hashes[0],
            "deterministic_setup": float(int(deterministic_setup)),
            "action_source": str(proof_config.selfplay_action_source),
            "alignment_positions": float(alignment.get("positions", 0.0)),
            "alignment_policy_ce": float(alignment.get("policy_ce", 0.0)),
            "alignment_top1_acc": float(alignment.get("top1_acc", 0.0)),
            "alignment_value_mse": float(alignment.get("value_mse", 0.0)),
            "alignment_value_sign_acc": float(alignment.get("value_sign_acc", 0.0)),
            "search_reward": float(search_rollout["reward"]),
            "search_turns": float(search_rollout["turns"]),
            "search_winner": float(search_rollout["winner"]),
            "search_fast_win": float(search_rollout["fast_win"]),
            "model_reward": float(model_rollout["reward"]),
            "model_turns": float(model_rollout["turns"]),
            "model_winner": float(model_rollout["winner"]),
            "model_fast_win": float(model_rollout["fast_win"]),
            "model_teacher_match_rate": float(model_rollout["teacher_match_rate"]),
            "model_search_agreement": float(model_rollout["model_teacher_match_rate"]),
        }
        if train_metrics is not None:
            row.update(
                {
                    "generated": float(train_metrics.get("generated", 0.0)),
                    "avg_reward": float(train_metrics.get("avg_reward", 0.0)),
                    "avg_turns": float(train_metrics.get("avg_turns", 0.0)),
                    "buffer_count": float(train_metrics.get("buffer_count", 0.0)),
                    "avg_loss": float(train_metrics.get("avg_loss", 0.0)),
                    "avg_policy_loss": float(train_metrics.get("avg_policy_loss", 0.0)),
                    "avg_value_loss": float(train_metrics.get("avg_value_loss", 0.0)),
                    "avg_policy_acc": float(train_metrics.get("avg_policy_acc", 0.0)),
                    "teacher_action_prob": float(train_metrics.get("teacher_action_prob", 0.0)),
                    "duration_sec": float(train_metrics.get("duration_sec", 0.0)),
                }
            )
        return row

    baseline_row = _capture_row(train_metrics=None)
    trainer._append_proof_row(baseline_row)
    rows.append(baseline_row)
    logger.info(
        "proof baseline: iteration=%s seed=%s align_top1=%.3f search_reward=%.3f model_reward=%.3f model_turns=%.2f",
        int(baseline_row["iteration"]),
        int(baseline_row["seed"]),
        float(baseline_row["alignment_top1_acc"]),
        float(baseline_row["search_reward"]),
        float(baseline_row["model_reward"]),
        float(baseline_row["model_turns"]),
    )

    for _ in range(int(proof_config.num_iterations)):
        train_metrics = trainer.train_iteration()
        row = _capture_row(train_metrics=train_metrics)
        trainer._append_proof_row(row)
        rows.append(row)
        logger.info(
            "proof iter=%s/%s seed=%s seed_it=%s generated=%s reward=%.3f align_top1=%.3f search_reward=%.3f model_reward=%.3f model_turns=%.2f loss=%.4f policy_acc=%.3f dur=%.2fs",
            int(row["iteration"]),
            int(proof_config.num_iterations),
            int(row["seed"]),
            int(train_metrics.get("seed_iteration", 0.0)),
            int(row.get("generated", 0.0)),
            float(row.get("avg_reward", 0.0)),
            float(row["alignment_top1_acc"]),
            float(row["search_reward"]),
            float(row["model_reward"]),
            float(row["model_turns"]),
            float(row.get("avg_loss", 0.0)),
            float(row.get("avg_policy_acc", 0.0)),
            float(row.get("duration_sec", 0.0)),
        )

    try:
        report = {
            "seed": int(seed),
            "deterministic_setup": bool(deterministic_setup),
            "setup_hash_samples": setup_hashes,
            "rows": _rounded(rows),
            "proof_log_csv": str(trainer.proof_log_csv_path),
            "proof_output_json": str(trainer.proof_output_json_path),
        }
        trainer.proof_output_json_path.parent.mkdir(parents=True, exist_ok=True)
        with trainer.proof_output_json_path.open("w", encoding="utf-8") as handle:
            json.dump(_rounded(report), handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        logger.info("Single-seed proof: %s", json.dumps(_rounded(report), indent=2))
        return report
    finally:
        trainer.close()


def run_search_ablation(config: OvernightConfig) -> dict[str, object]:
    base_config = config
    mcts_config = copy.deepcopy(base_config)
    mcts_config.training_target_mode = "neural_mcts"
    policy_config = copy.deepcopy(base_config)
    policy_config.training_target_mode = "selfplay"
    mcts_trainer = VanillaSelfPlayTrainer(mcts_config)
    policy_trainer = VanillaSelfPlayTrainer(policy_config)

    head_to_head = {
        "games": 0,
        "mcts_wins": 0,
        "policy_wins": 0,
        "draws": 0,
        "mcts_win_turn_sum": 0.0,
        "policy_win_turn_sum": 0.0,
    }
    total_games = max(2, int(config.benchmark_games))
    for game_idx in range(total_games):
        seed = int(config.benchmark_seed_base) + 100_000 + game_idx
        state = mcts_trainer._new_state(seed)
        _apply_deterministic_setup(state, mcts_trainer.rust_db)
        while not state.is_terminal() and int(state.turn) < mcts_trainer.config.max_turns:
            legal_ids = [int(action_id) for action_id in state.get_legal_action_ids()]
            if not legal_ids:
                state.auto_step(mcts_trainer.rust_db)
                continue
            if int(state.current_player) == 0:
                action = mcts_trainer._choose_neural_mcts_action(state, legal_ids)
            else:
                action = policy_trainer._choose_model_eval_action_with_model(state, legal_ids, policy_trainer.model)
            state.step(int(action))
            state.auto_step(mcts_trainer.rust_db)
        winner = int(state.get_winner()) if state.is_terminal() else -1
        head_to_head["games"] += 1
        if winner == 0:
            head_to_head["mcts_wins"] += 1
            head_to_head["mcts_win_turn_sum"] += float(state.turn)
        elif winner == 1:
            head_to_head["policy_wins"] += 1
            head_to_head["policy_win_turn_sum"] += float(state.turn)
        else:
            head_to_head["draws"] += 1

    if head_to_head["mcts_wins"] > 0:
        head_to_head["avg_mcts_win_turns"] = head_to_head["mcts_win_turn_sum"] / head_to_head["mcts_wins"]
    else:
        head_to_head["avg_mcts_win_turns"] = 0.0
    if head_to_head["policy_wins"] > 0:
        head_to_head["avg_policy_win_turns"] = head_to_head["policy_win_turn_sum"] / head_to_head["policy_wins"]
    else:
        head_to_head["avg_policy_win_turns"] = 0.0
    head_to_head.pop("mcts_win_turn_sum")
    head_to_head.pop("policy_win_turn_sum")

    suite = {
        "head_to_head": head_to_head,
        "mcts_vs_greedy": mcts_trainer.benchmark_matchup("greedy", games=total_games, seed_base=int(config.benchmark_seed_base)),
        "policy_vs_greedy": policy_trainer.benchmark_matchup("greedy", games=total_games, seed_base=int(config.benchmark_seed_base)),
        "mcts_vs_search": mcts_trainer.benchmark_matchup("search", games=total_games, seed_base=int(config.benchmark_seed_base) + 50_000),
        "policy_vs_search": policy_trainer.benchmark_matchup("search", games=total_games, seed_base=int(config.benchmark_seed_base) + 50_000),
    }
    logger.info("Search ablation summary: %s", json.dumps(_rounded(suite), indent=2))
    return suite


def run_mine_hard_seeds(config: OvernightConfig) -> dict[str, object]:
    trainer = VanillaSelfPlayTrainer(config)
    try:
        rows: list[dict[str, object]] = []
        min_turns = min(int(config.max_turns), int(config.hard_seed_min_turns))
        for game_idx in range(int(config.hard_seed_scan_games)):
            seed = int(config.seed) + game_idx
            result = trainer.play_self_play_game(seed)
            live_margin = abs(int(result.p0_lives) - int(result.p1_lives))
            score_margin = abs(int(result.p0_score) - int(result.p1_score))
            is_draw = int(result.winner) == -1
            near_cap = int(result.turns) >= min_turns
            near_margin = live_margin <= 1 or score_margin <= 1
            if not (is_draw or (near_cap and near_margin)):
                continue
            rows.append(
                {
                    "seed": int(seed),
                    "winner": int(result.winner),
                    "turns": int(result.turns),
                    "p0_lives": int(result.p0_lives),
                    "p1_lives": int(result.p1_lives),
                    "p0_score": int(result.p0_score),
                    "p1_score": int(result.p1_score),
                    "records": int(len(result.records)),
                }
            )

        path = trainer._focus_seed_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at_unix": time.time(),
            "seed_start": int(config.seed),
            "scan_games": int(config.hard_seed_scan_games),
            "max_turns": int(config.max_turns),
            "hard_seed_min_turns": int(min_turns),
            "seeds": [int(row["seed"]) for row in rows],
            "rows": rows,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        summary = {
            "seed_file": str(path.relative_to(ROOT_DIR)) if path.is_relative_to(ROOT_DIR) else str(path),
            "scan_games": int(config.hard_seed_scan_games),
            "hard_seed_count": len(rows),
            "draw_count": sum(1 for row in rows if int(row["winner"]) == -1),
            "sample": rows[: min(8, len(rows))],
        }
        logger.info("Hard seed summary: %s", json.dumps(_rounded(summary), indent=2))
        return summary
    finally:
        trainer.close()


def run_audit(config: OvernightConfig, max_decisions: int = 10) -> dict[str, object]:
    trainer = VanillaSelfPlayTrainer(config)
    try:
        summary = trainer.audit_game(config.seed, max_decisions=max_decisions)
        logger.info("Audit summary: %s", json.dumps(_rounded(summary), indent=2))
        return summary
    finally:
        trainer.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Vanilla self-play trainer")
    parser.add_argument("command", nargs="?", default="train", choices=["train", "smoke", "proof", "single_seed_proof", "benchmark", "audit", "ablation", "mine_seeds", "certify"])
    parser.add_argument("--iterations", type=int, default=None)
    parser.add_argument("--games", type=int, default=None)
    parser.add_argument("--steps", type=int, default=None)
    parser.add_argument("--search-sims", type=int, default=None)
    parser.add_argument("--neural-mcts-batch-size", type=int, default=None)
    parser.add_argument("--max-turns", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--buffer-size", type=int, default=None)
    parser.add_argument("--min-buffer-items", type=int, default=None)
    parser.add_argument("--actor-temperature", type=float, default=None)
    parser.add_argument("--actor-epsilon", type=float, default=None)
    parser.add_argument("--teacher-action-prob", type=float, default=None)
    parser.add_argument("--min-teacher-action-prob", type=float, default=None)
    parser.add_argument("--teacher-action-warmup-iters", type=int, default=None)
    parser.add_argument("--teacher-action-decay-iters", type=int, default=None)
    parser.add_argument("--benchmark-games", type=int, default=None)
    parser.add_argument("--benchmark-model-search-sims", type=int, default=None)
    parser.add_argument("--benchmark-search-sims", type=int, default=None)
    parser.add_argument("--benchmark-every", type=int, default=None)
    parser.add_argument("--turnseq-benchmark-games", type=int, default=None)
    parser.add_argument("--reference-benchmark-games", type=int, default=None)
    parser.add_argument("--target-replay-ratio", type=float, default=None)
    parser.add_argument("--audit-decisions", type=int, default=10)
    parser.add_argument("--deck-rotation-mode", type=str, choices=["single", "per_iteration"], default=None)
    parser.add_argument("--selfplay-seed-mode", type=str, choices=["random", "focus_mix", "focus_only", "curriculum_single", "fixed_single"], default=None)
    parser.add_argument("--hard-seed-file", type=str, default=None)
    parser.add_argument("--hard-seed-ratio", type=float, default=None)
    parser.add_argument("--hard-seed-scan-games", type=int, default=None)
    parser.add_argument("--hard-seed-min-turns", type=int, default=None)
    parser.add_argument("--single-seed-plateau-window", type=int, default=None)
    parser.add_argument("--single-seed-plateau-delta", type=float, default=None)
    parser.add_argument("--single-seed-min-iters", type=int, default=None)
    parser.add_argument("--single-seed-max-iters", type=int, default=None)
    parser.add_argument("--curriculum-eval-games", type=int, default=None)
    parser.add_argument("--single-seed-target-reward", type=float, default=None)
    parser.add_argument("--single-seed-target-decisive-rate", type=float, default=None)
    parser.add_argument("--single-seed-target-fast-win-rate", type=float, default=None)
    parser.add_argument("--single-seed-target-avg-turns", type=float, default=None)
    parser.add_argument("--single-seed-fast-turn-threshold", type=int, default=None)
    parser.add_argument("--skip-draw-records", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--selfplay-action-source", type=str, choices=["search_sample", "search_greedy", "model_sample", "model_greedy", "hybrid_teacher"], default=None)
    parser.add_argument("--reset-training-state", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--proof-eval-games", type=int, default=None)
    parser.add_argument("--checkpoint-dir", type=str, default=None)
    parser.add_argument("--buffer-dir", type=str, default=None)
    parser.add_argument("--log-csv", type=str, default=None)
    parser.add_argument("--benchmark-log-csv", type=str, default=None)
    parser.add_argument("--active-deck-name", type=str, default=None)
    parser.add_argument("--proof-log-csv", type=str, default=None)
    parser.add_argument("--proof-output-json", type=str, default=None)
    parser.add_argument("--model-preset", type=str, default=None)
    parser.add_argument("--training-target-mode", type=str, choices=["selfplay", "search", "neural_mcts"], default=None)
    parser.add_argument("--observation-mode", type=str, choices=[OBSERVATION_MODE_RAW, OBSERVATION_MODE_HINT, OBSERVATION_MODE_FULL], default=None)
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--seed", type=int, default=None)
    return parser


def _apply_cli_overrides(config: OvernightConfig, args: argparse.Namespace) -> OvernightConfig:
    data = asdict(config)
    if args.iterations is not None:
        data["num_iterations"] = args.iterations
    if args.games is not None:
        if args.command == "proof":
            data["proof_games"] = args.games
        else:
            data["games_per_iteration"] = args.games
    if args.steps is not None:
        if args.command == "proof":
            data["proof_train_steps"] = args.steps
        else:
            data["training_steps_per_iteration"] = args.steps
    if args.search_sims is not None:
        data["search_sims"] = args.search_sims
    if args.neural_mcts_batch_size is not None:
        data["neural_mcts_batch_size"] = args.neural_mcts_batch_size
    if args.max_turns is not None:
        data["max_turns"] = args.max_turns
    if args.batch_size is not None:
        data["batch_size"] = args.batch_size
    if args.buffer_size is not None:
        data["buffer_size"] = args.buffer_size
    if args.min_buffer_items is not None:
        data["min_buffer_items"] = args.min_buffer_items
    if args.actor_temperature is not None:
        data["actor_temperature"] = args.actor_temperature
    if args.actor_epsilon is not None:
        data["actor_epsilon"] = args.actor_epsilon
    if args.teacher_action_prob is not None:
        data["teacher_action_prob"] = args.teacher_action_prob
    if args.min_teacher_action_prob is not None:
        data["min_teacher_action_prob"] = args.min_teacher_action_prob
    if args.teacher_action_warmup_iters is not None:
        data["teacher_action_warmup_iters"] = args.teacher_action_warmup_iters
    if args.teacher_action_decay_iters is not None:
        data["teacher_action_decay_iters"] = args.teacher_action_decay_iters
    if args.benchmark_games is not None:
        data["benchmark_games"] = args.benchmark_games
    if args.benchmark_model_search_sims is not None:
        data["benchmark_model_search_sims"] = args.benchmark_model_search_sims
    if args.benchmark_search_sims is not None:
        data["benchmark_search_sims"] = args.benchmark_search_sims
    if args.benchmark_every is not None:
        data["benchmark_every"] = args.benchmark_every
    if args.turnseq_benchmark_games is not None:
        data["turnseq_benchmark_games"] = args.turnseq_benchmark_games
    if args.reference_benchmark_games is not None:
        data["reference_benchmark_games"] = args.reference_benchmark_games
    if args.target_replay_ratio is not None:
        data["target_replay_ratio"] = args.target_replay_ratio
    if args.deck_rotation_mode is not None:
        data["deck_rotation_mode"] = args.deck_rotation_mode
    if args.selfplay_seed_mode is not None:
        data["selfplay_seed_mode"] = args.selfplay_seed_mode
    if args.hard_seed_file is not None:
        data["hard_seed_file"] = args.hard_seed_file
    if args.hard_seed_ratio is not None:
        data["hard_seed_ratio"] = args.hard_seed_ratio
    if args.hard_seed_scan_games is not None:
        data["hard_seed_scan_games"] = args.hard_seed_scan_games
    if args.hard_seed_min_turns is not None:
        data["hard_seed_min_turns"] = args.hard_seed_min_turns
    if args.single_seed_plateau_window is not None:
        data["single_seed_plateau_window"] = args.single_seed_plateau_window
    if args.single_seed_plateau_delta is not None:
        data["single_seed_plateau_delta"] = args.single_seed_plateau_delta
    if args.single_seed_min_iters is not None:
        data["single_seed_min_iters"] = args.single_seed_min_iters
    if args.single_seed_max_iters is not None:
        data["single_seed_max_iters"] = args.single_seed_max_iters
    if args.curriculum_eval_games is not None:
        data["curriculum_eval_games"] = args.curriculum_eval_games
    if args.single_seed_target_reward is not None:
        data["single_seed_target_reward"] = args.single_seed_target_reward
    if args.single_seed_target_decisive_rate is not None:
        data["single_seed_target_decisive_rate"] = args.single_seed_target_decisive_rate
    if args.single_seed_target_fast_win_rate is not None:
        data["single_seed_target_fast_win_rate"] = args.single_seed_target_fast_win_rate
    if args.single_seed_target_avg_turns is not None:
        data["single_seed_target_avg_turns"] = args.single_seed_target_avg_turns
    if args.single_seed_fast_turn_threshold is not None:
        data["single_seed_fast_turn_threshold"] = args.single_seed_fast_turn_threshold
    if args.skip_draw_records is not None:
        data["skip_draw_records"] = args.skip_draw_records
    if args.selfplay_action_source is not None:
        data["selfplay_action_source"] = args.selfplay_action_source
    if args.reset_training_state is not None:
        data["reset_training_state"] = args.reset_training_state
    if args.proof_eval_games is not None:
        data["proof_eval_games"] = args.proof_eval_games
    if args.checkpoint_dir is not None:
        data["checkpoint_dir"] = args.checkpoint_dir
    if args.buffer_dir is not None:
        data["buffer_dir"] = args.buffer_dir
    if args.log_csv is not None:
        data["log_csv"] = args.log_csv
    if args.benchmark_log_csv is not None:
        data["benchmark_log_csv"] = args.benchmark_log_csv
    if args.active_deck_name is not None:
        data["active_deck_name"] = args.active_deck_name
    if args.proof_log_csv is not None:
        data["proof_log_csv"] = args.proof_log_csv
    if args.proof_output_json is not None:
        data["proof_output_json"] = args.proof_output_json
    if args.model_preset is not None:
        data["model_preset"] = args.model_preset
    if args.training_target_mode is not None:
        data["training_target_mode"] = args.training_target_mode
    if args.observation_mode is not None:
        data["observation_mode"] = args.observation_mode
    if args.device is not None:
        data["device"] = args.device
    if args.seed is not None:
        data["seed"] = args.seed
    return OvernightConfig(**data)


def main(argv: Sequence[str] | None = None):
    _configure_logging()
    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    config = _apply_cli_overrides(OvernightConfig(), args)
    if args.command == "smoke":
        return run_smoke(config)
    if args.command == "proof":
        return run_learning_proof(config)
    if args.command == "single_seed_proof":
        return run_single_seed_proof(config)
    if args.command == "benchmark":
        return run_benchmark(config)
    if args.command == "audit":
        return run_audit(config, max_decisions=args.audit_decisions)
    if args.command == "ablation":
        return run_search_ablation(config)
    if args.command == "mine_seeds":
        return run_mine_hard_seeds(config)
    if args.command == "certify":
        return run_certify(config, games=args.games)
    trainer = VanillaSelfPlayTrainer(config)
    trainer.run()
    return None


if __name__ == "__main__":
    main()