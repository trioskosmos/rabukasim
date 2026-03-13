from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import random
import shutil
import sys
import time
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

import numpy as np
import torch
import torch.nn.functional as F
from torch import optim

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Find the compiled Rust extension before importing engine_rust.
for candidate in (
    ROOT_DIR / "engine_rust_src" / "target" / "release",
    ROOT_DIR / "engine_rust_src" / "target" / "dev-release",
    ROOT_DIR / "engine_rust_src" / "target" / "debug",
):
    if (candidate / "engine_rust.pyd").exists() or (candidate / "engine_rust.dll").exists():
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
        break

import engine_rust
from engine.game.deck_utils import UnifiedDeckParser

from alphazero.training.disk_buffer import PersistentBuffer
from alphazero.training.vanilla_action_codec import (
    ACTION_SPACE,
    build_legal_policy_mask,
    build_policy_engine_mapping,
    dense_to_sparse,
    sparse_policy_from_engine_visits,
)
from alphazero.training.vanilla_observation import OBS_DIM, build_card_feature_lookup, build_vanilla_observation
from alphazero.vanilla_net import (
    HighFidelityAlphaNet,
    VanillaTransformerConfig,
    choose_vanilla_config_for_budget,
)

DEFAULT_BUFFER_DIR = ROOT_DIR / "alphazero" / "training" / "experience_vanilla"
DEFAULT_CHECKPOINT_DIR = ROOT_DIR / "alphazero" / "training" / "vanilla_checkpoints"
DEFAULT_DB_PATH = ROOT_DIR / "data" / "cards_compiled.json"
DEFAULT_DECK_DIR = ROOT_DIR / "ai" / "decks"
PHASE_MAIN = 4
PHASE_LIVE_SET = 5

_WORKER_DB = None
_WORKER_MODEL = None
_WORKER_EVALUATOR = None
_WORKER_CONFIG: dict[str, Any] | None = None
_WORKER_DEVICE: torch.device | None = None
_WORKER_CARD_LOOKUP: dict[int, dict[str, Any]] | None = None

warnings.filterwarnings(
    "ignore",
    message="enable_nested_tensor is True, but self.use_nested_tensor is False because encoder_layer.norm_first was True",
    category=UserWarning,
)


@dataclass(frozen=True)
class OvernightConfig:
    """Complete configuration for overnight training pipeline.
    
    ===== SELF-PLAY PARAMETERS (game generation) =====
    games_per_cycle (int): Total games to generate per training cycle (default 64)
    workers (int): Number of parallel worker processes (default 8)
    sims_per_move (int): MCTS simulations per action, higher = stronger but slower (default 128)
    mcts_batch_size (int): Batch size for neural network inference in MCTS (default 128)
    max_turns (int): Max game length to prevent infinite loops (default 10)
    max_moves (int): Max total action count across both players (default 160)
    exploration_turns (int): First N turns use temperature > 0 for diversity (default 4)
    root_dirichlet_alpha (float): Dirichlet noise alpha parameter (default 0.30)
    root_dirichlet_eps (float): Dirichlet noise strength (0.0 = none, 1.0 = full noise) (default 0.20)
    temperature (float): Action sampling temperature (0.0=greedy, 1.0=uniform) (default 1.0)
    teacher_mix (float): Blend between model policy and heuristic MCTS visits [0-1] (default 0.35)
    
    ===== TRAINING PARAMETERS =====
    batch_size (int): Training batch size, limited by GPU memory (default 256)
    train_steps_per_cycle (int): Gradient descent steps per training cycle (default 48)
    learning_rate (float): Adam optimizer learning rate (default 3e-4)
    weight_decay (float): L2 regularization coefficient (default 1e-4)
    grad_clip (float): Gradient clipping threshold (default 1.0)
    entropy_bonus (float): Policy entropy regularization weight (default 3e-4)
    aux_value_weight (float): Weight for auxiliary value losses (default 0.35)
    buffer_size (int): Max replay buffer capacity stored on disk (default 120k)
    sparse_limit (int): Max non-zero actions per policy vector, memory efficient (default 32)
    min_buffer_samples (int): Warmup samples required before starting SGD (default 4096)
    
    ===== MODEL PARAMETERS =====
    model_preset (str): One of (tiny, small, base, large, budget) (default "small")
    model_budget_millions (float): Alternative: auto-size model to fit budget in MB (default 2.5)
    
    ===== CYCLE CONTROL =====
    cycles (int): Total training cycles to run (default 200)
    max_hours (float): Wall-clock timeout in hours (0 = no limit) (default 10.0)
    checkpoint_every_cycles (int): Save archival checkpoint every N cycles (default 5)
    save_latest_every_cycles (int): Save latest checkpoint every N cycles (default 1)
    
    ===== ARENA EVALUATION (validates improvement, prevents deck luck) =====
    arena_size (int): Games per arena match (0 = disabled) (default 0)
    arena_win_threshold (float): Required win% to promote model (0.55 = 55%) (default 0.55)
    arena_every_cycles (int): Run arena evaluation every N training cycles (default 10)
    benchmark_every_cycles (int): Run fixed benchmark suite every N cycles (0 = disabled) (default 5)
    benchmark_games (int): Games per benchmark opponent with seat swaps (default 16)
    KEY FEATURE: Uses same deck pairs for all games to control for deck matchup luck
    
    ===== SYSTEM PARAMETERS =====
    device (str): 'cuda' (GPU), 'cpu', or 'auto' (detect available) (default "cuda")
    seed (int): Random seed for reproducibility (default 1337)
    resume (bool): Resume existing checkpoint/buffer directories instead of requiring a clean run (default False)
    run_name (str): Identifier for logs and checkpoints (default "vanilla_overnight")
    db_path (str): Path to cards database JSON (default computed from ROOT_DIR)
    deck_dir (str): Path to deck files directory (default computed from ROOT_DIR)
    buffer_dir (str): Path to replay buffer storage (default computed from ROOT_DIR)
    checkpoint_dir (str): Path to model checkpoints (default computed from ROOT_DIR)
    mirror_matches (bool): Reserved for future multi-model tournaments (default False)
    """
    mode: str = "overnight"
    run_name: str = "vanilla_overnight"
    db_path: str = str(DEFAULT_DB_PATH)
    deck_dir: str = str(DEFAULT_DECK_DIR)
    buffer_dir: str = str(DEFAULT_BUFFER_DIR)
    checkpoint_dir: str = str(DEFAULT_CHECKPOINT_DIR)
    cycles: int = 200
    max_hours: float = 10.0
    games_per_cycle: int = 32
    workers: int = 8
    sims_per_move: int = 128
    mcts_batch_size: int = 128
    max_turns: int = 12
    max_moves: int = 160
    exploration_turns: int = 4
    root_dirichlet_alpha: float = 0.30
    root_dirichlet_eps: float = 0.20
    temperature: float = 1.0
    teacher_mix: float = 1.0
    batch_size: int = 256
    train_steps_per_cycle: int = 48
    learning_rate: float = 3e-4
    weight_decay: float = 1e-4
    grad_clip: float = 1.0
    entropy_bonus: float = 3e-4
    aux_value_weight: float = 0.35
    buffer_size: int = 120_000
    sparse_limit: int = 32
    min_buffer_samples: int = 4_096
    checkpoint_every_cycles: int = 5
    save_latest_every_cycles: int = 1
    model_preset: str = "small"
    model_budget_millions: float = 2.5
    device: str = "cuda"
    seed: int = 1337
    fixed_cycle_seed: bool = False
    reset_run: bool = False
    freeze_selfplay_after_cycle_one: bool = False
    mcts_only_selfplay: bool = False
    resume: bool = False
    mirror_matches: bool = False
    arena_size: int = 0
    arena_win_threshold: float = 0.55
    arena_every_cycles: int = 10
    benchmark_every_cycles: int = 5
    benchmark_games: int = 16

    def resolved_device(self) -> str:
        if self.device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        if self.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError(
                "OvernightConfig requested device='cuda' but CUDA is not available in the active Python environment. "
                "Use 'uv run python ...' for the repo CUDA environment or switch to --device cpu."
            )
        return self.device


def _torch_device(name: str) -> torch.device:
    return torch.device(name)


def _configure_torch_runtime(device: torch.device) -> None:
    if device.type != "cuda":
        return
    torch.backends.cudnn.benchmark = True
    torch.set_float32_matmul_precision("high")


def _extract_checkpoint_state_dict(checkpoint: dict[str, Any] | dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    state_dict = checkpoint.get("model", checkpoint)
    if not isinstance(state_dict, dict):
        raise RuntimeError(f"Checkpoint model payload must be a state_dict dict, got {type(state_dict)!r}")
    return state_dict


def _remap_state_dict_for_model(
    state_dict: dict[str, torch.Tensor],
    model: torch.nn.Module,
) -> dict[str, torch.Tensor]:
    expected_keys = set(model.state_dict().keys())
    source_keys = set(state_dict.keys())
    if source_keys == expected_keys:
        return state_dict

    if source_keys and all(key.startswith("net.") for key in source_keys):
        stripped = {key[4:]: value for key, value in state_dict.items() if key.startswith("net.")}
        if set(stripped.keys()) == expected_keys:
            return stripped

    prefixed = {f"net.{key}": value for key, value in state_dict.items()}
    if set(prefixed.keys()) == expected_keys:
        return prefixed

    missing = sorted(expected_keys - source_keys)
    unexpected = sorted(source_keys - expected_keys)
    raise RuntimeError(
        "Checkpoint model keys do not match the target model. "
        f"Missing sample: {missing[:5]} Unexpected sample: {unexpected[:5]}"
    )


def _load_checkpoint_into_model(
    model: torch.nn.Module,
    checkpoint: dict[str, Any] | dict[str, torch.Tensor],
) -> None:
    state_dict = _extract_checkpoint_state_dict(checkpoint)
    model.load_state_dict(_remap_state_dict_for_model(state_dict, model))


def _read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_vanilla_database_json(db_path: str | Path) -> tuple[dict[str, Any], str]:
    """Load card database and create stripped JSON for Rust engine (auto-cached on disk).
    
    PROCESS:
      1. Load full JSON from db_path (cards_compiled.json)
      2. Create stripped copy: removes all ability/synergy data that Rust engine doesn't use
      3. Return both: full_db (Python dict) and stripped (JSON string for Rust)
    
    RATIONALE FOR STRIPPING:
      Rust engine needs minimal metadata: card IDs, factions, types, energy cost
      Removing abilities/synergies: reduces memory footprint, speeds Rust serialization
      Kept in Python side: useful for logging, analysis, but not needed in real-time engine
    
    Args:
      db_path: Path to cards_compiled.json (typically data/cards_compiled.json)
    
    Returns:
      (full_db, stripped_json): Full Python dict and JSON string for Rust engine
      full_db: Has abilities/flags intact (used for Python analysis)
      stripped_json: Abilities removed, optimized for Rust PyCardDatabase
    
    Auto-save: Stripped JSON cached in Rust PyCardDatabase constructor call
    """
    full_db = _read_json(db_path)
    stripped = json.loads(json.dumps(full_db))
    for category in ("member_db", "live_db"):
        for data in stripped.get(category, {}).values():
            data["abilities"] = []
            data["ability_flags"] = 0
            if "synergy_flags" in data:
                data["synergy_flags"] &= 1
    return stripped, json.dumps(stripped)


def load_tournament_decks(full_db: dict[str, Any], deck_dir: str | Path | None = None) -> list[dict[str, Any]]:
    """Load tournament-format decks from text files on disk (auto-cached via UnifiedDeckParser).
    
    DECK FILE FORMAT (text, one card per line):
      - Each deck must have ≥30 members and ≥6 lives cards
      - Format: "Card Name" or "Card ID" or deck list notation
      - UnifiedDeckParser resolves to standard card IDs
    
    DECK COMPOSITION (after loading):
      - members (48 cards): Main deck cards, padded via cycling if needed
      - lives (12 cards): Starter cards, padded via cycling if needed
      - energy (12 cards): Energy cards, filled with standard pool if missing
      - initial_deck: Concatenation of members + lives (shuffled by engine during play)
    
    VALIDATION & LOADING:
      1. Scan deck_dir/ for all *.txt files (sorted for determinism)
      2. For each file:
         - Parse content using UnifiedDeckParser (card name → card ID)
         - Separate into Member / Live / Energy types
         - Skip if < 30 members or < 6 lives (malformed deck)
      3. Cycle decks to standard sizes (48 members, 12 lives, 12 energy)
      4. Return list of valid dicts with keys: name, members, lives, energy, initial_deck
    
    WHY CYCLING (padding):
      If deck has 32 members: cycle [m1, m2, ..., m32] twice, take first 48 → repeats cards
      Ensures deterministic 40-card deck (48+12 members+lives = shuffled into 40-card hand)
      Predictable behavior across training runs
    
    Args:
      full_db: Card database dict (returned by load_vanilla_database_json)
      deck_dir: Directory with *.txt files (default: ai/decks)
    
    Returns:
      List of deck dicts, each with: name, members, lives, energy, initial_deck
      At least 1 valid deck must exist, else raises RuntimeError
    
    Auto-save: Deck files cached on disk (deck_dir), no additional save needed here
    """
    deck_dir = Path(deck_dir or DEFAULT_DECK_DIR)
    parser = UnifiedDeckParser(full_db)
    loaded_decks: list[dict[str, Any]] = []
    standard_energy_ids = [38, 39, 40, 41, 42] * 4

    for deck_file in sorted(deck_dir.glob("*.txt")):
        try:
            content = deck_file.read_text(encoding="utf-8")
        except OSError:
            continue
        parsed = parser.extract_from_content(content)
        if not parsed:
            continue

        entry = parsed[0]
        members: list[int] = []
        lives: list[int] = []
        energy: list[int] = []

        for card_no in entry.get("main", []):
            resolved = parser.resolve_card(card_no)
            if not resolved:
                continue
            if resolved.get("type") == "Member":
                members.append(resolved["card_id"])
            elif resolved.get("type") == "Live":
                lives.append(resolved["card_id"])

        for card_no in entry.get("energy", []):
            resolved = parser.resolve_card(card_no)
            if resolved:
                energy.append(resolved["card_id"])

        if len(members) < 30 or len(lives) < 6:
            continue

        members = (members + members * 4)[:48]
        lives = (lives + lives * 4)[:12]
        energy = (energy + standard_energy_ids * 12)[:12]
        loaded_decks.append(
            {
                "name": deck_file.stem,
                "members": members,
                "lives": lives,
                "energy": energy,
                "initial_deck": members + lives,
            }
        )

    if not loaded_decks:
        raise RuntimeError(f"No valid decks found under {deck_dir}")
    return loaded_decks


class VanillaPolicyModel(torch.nn.Module):
    def __init__(self, config: VanillaTransformerConfig):
        super().__init__()
        self.net = HighFidelityAlphaNet(config=config)

    @property
    def config(self) -> VanillaTransformerConfig:
        return self.net.config

    def forward(self, obs: torch.Tensor, mask: Optional[torch.Tensor] = None):
        return self.net(obs, mask=mask)

    def parameter_count(self) -> int:
        return self.net.parameter_count()

    def parameter_count_millions(self) -> float:
        return self.net.parameter_count_millions()

    def describe(self) -> dict[str, Any]:
        return self.net.describe()

    def predict_batch(self, tensors: Iterable[Sequence[float]]):
        device = next(self.parameters()).device
        obs_t = torch.as_tensor(list(tensors), dtype=torch.float32, device=device)
        mask_t = torch.ones((obs_t.size(0), ACTION_SPACE), dtype=torch.bool, device=device)
        with torch.inference_mode():
            logits, values = self.forward(obs_t, mask_t)
            probs = torch.softmax(logits, dim=1).cpu().numpy().tolist()
            win_values = torch.sigmoid(values[:, 0]).cpu().numpy().tolist()
        heuristic_weights = [[1.0] * 17 for _ in range(obs_t.size(0))]
        return win_values, probs, heuristic_weights


@dataclass(frozen=True)
class SelfPlayStats:
    deck_a: str
    deck_b: str
    winner: int
    turns: int
    moves: int
    p0_success: int
    p1_success: int
    decision_points: int
    planner_guided_points: int
    duration_secs: float


@dataclass(frozen=True)
class CycleSummary:
    cycle: int
    games: int
    decisive_games: int
    avg_turns: float
    decisive_avg_turns: float
    avg_duration_secs: float
    p0_success_avg: float
    p1_success_avg: float
    draw_rate: float
    planner_guided_ratio: float
    buffer_count: int
    train_loss: float
    policy_loss: float
    value_loss: float


@dataclass(frozen=True)
class SelfPlayGameStats:
    winner: int
    turns: int
    p0_success: int
    p1_success: int
    decided: bool


def _zero_train_stats() -> dict[str, float]:
    return {"loss": 0.0, "policy": 0.0, "value": 0.0}


def _assert_run_paths_ready(config: OvernightConfig) -> None:
    if config.resume:
        return

    conflicts: list[str] = []
    latest_path = Path(config.checkpoint_dir) / "latest.pt"
    buffer_meta = Path(config.buffer_dir) / "meta.json"
    if latest_path.exists():
        conflicts.append(str(latest_path))
    if buffer_meta.exists():
        conflicts.append(str(buffer_meta))

    if conflicts:
        joined = ", ".join(conflicts)
        raise RuntimeError(
            "Refusing to reuse an existing training run without --resume. "
            f"Conflicting paths: {joined}"
        )


def _prepare_run_paths(config: OvernightConfig) -> None:
    if config.resume or not config.reset_run:
        return

    checkpoint_dir = Path(config.checkpoint_dir)
    buffer_dir = Path(config.buffer_dir)
    if checkpoint_dir.exists():
        shutil.rmtree(checkpoint_dir)
    if buffer_dir.exists():
        shutil.rmtree(buffer_dir)


def _print_cycle_summary(summary: CycleSummary, cycle_secs: float) -> None:
    decisive_rate = (summary.decisive_games / summary.games) if summary.games else 0.0
    games_per_sec = (summary.games / cycle_secs) if cycle_secs > 0 else 0.0
    print(
        f"[CYCLE {summary.cycle}] "
        f"games={summary.games} decisive={summary.decisive_games}/{summary.games} ({decisive_rate:.0%}) "
        f"avg_game={summary.avg_duration_secs:.2f}s avg_turns={summary.avg_turns:.2f} "
        f"decisive_avg_turns={summary.decisive_avg_turns:.2f} draw_rate={summary.draw_rate:.0%} "
        f"planner={summary.planner_guided_ratio:.0%} "
        f"cycle_time={cycle_secs:.1f}s games_per_sec={games_per_sec:.2f} "
        f"buffer={summary.buffer_count} "
        f"loss={summary.train_loss:.4f} policy={summary.policy_loss:.4f} value={summary.value_loss:.4f}",
        flush=True,
    )


class ReplayTrainer:
    def __init__(self, config: OvernightConfig, model: VanillaPolicyModel, device: torch.device):
        self.config = config
        self.model = model
        self.device = device
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )

    def train_steps(self, buffer: PersistentBuffer, steps: int) -> dict[str, float]:
        self.model.train()
        totals = {"loss": 0.0, "policy": 0.0, "value": 0.0}
        actual_steps = 0

        for _ in range(steps):
            batch = buffer.sample(self.config.batch_size)
            if batch is None:
                break
            obs_np, sparse_pol, mask_np, targets_np = batch
            batch_size = int(obs_np.shape[0])

            obs_t = torch.as_tensor(obs_np, dtype=torch.float32, device=self.device)
            mask_t = torch.as_tensor(mask_np, dtype=torch.bool, device=self.device)
            targets_t = torch.as_tensor(targets_np, dtype=torch.float32, device=self.device)
            policy_targets = torch.zeros((batch_size, ACTION_SPACE), dtype=torch.float32, device=self.device)
            row_idx, col_idx, values = sparse_pol
            if len(values) > 0:
                policy_targets[
                    torch.as_tensor(row_idx, dtype=torch.long, device=self.device),
                    torch.as_tensor(col_idx, dtype=torch.long, device=self.device),
                ] = torch.as_tensor(values, dtype=torch.float32, device=self.device)

            self.optimizer.zero_grad(set_to_none=True)
            policy_logits, value_outputs = self.model(obs_t, mask_t)

            log_probs = F.log_softmax(policy_logits, dim=1)
            policy_loss = -(policy_targets * log_probs).sum(dim=1).mean()
            win_loss = F.binary_cross_entropy_with_logits(value_outputs[:, 0], targets_t[:, 0].clamp(0.0, 1.0))
            aux_loss = F.mse_loss(torch.tanh(value_outputs[:, 1:]), targets_t[:, 1:])
            entropy = -(torch.softmax(policy_logits, dim=1) * log_probs).sum(dim=1).mean()
            value_loss = win_loss + self.config.aux_value_weight * aux_loss
            loss = policy_loss + value_loss - self.config.entropy_bonus * entropy

            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.grad_clip)
            self.optimizer.step()

            totals["loss"] += float(loss.item())
            totals["policy"] += float(policy_loss.item())
            totals["value"] += float(value_loss.item())
            actual_steps += 1

        if actual_steps == 0:
            return totals
        for key in totals:
            totals[key] /= actual_steps
        return totals


class SelfPlayCoordinator:
    """Orchestrate parallel self-play game generation using ProcessPoolExecutor.
    
    ROLE:
      Manages multi-process self-play: generates config.games_per_cycle games in parallel
      Each game uses MCTS with neural evaluator (Phase 1) or fallback heuristic MCTS
      Returns game transitions (state, policy, value targets) for training
    
    PARALLEL ARCHITECTURE:
      - ProcessPoolExecutor with config.workers worker processes
      - Each worker initializes with _init_self_play_worker (one-time setup)
      - Workers pull from task queue asynchronously via executor.submit
      - Main process collects results as they complete (as_completed)
    
    MATCHUP SELECTION:
      - Each game samples random deck pair (or same deck for mirrors)
      - Sampling: random.Random(cycle_seed + game_idx) for reproducibility
      - Deck pairs: (player0_deck, player1_deck) from tournament deck pool
      - Can enable config.mirror_matches for homogeneous testing
    
    AUTO-SAVE COORDINATION:
      - Loads latest checkpoint (latest.pt) at cycle start
      - All workers use same model version during one cycle
      - Between cycles: save new checkpoint → all next-cycle workers see updated model
      - Ensures checkpoint mutations are visible to new workers
    
    Args (init):
      config: OvernightConfig with games_per_cycle, workers, deck_dir, etc.
      model_config: VanillaTransformerConfig (passed to workers for model rebuild)
    """

    def __init__(self, config: OvernightConfig, model_config: VanillaTransformerConfig):
        self.config = config
        self.model_config = model_config
        self.db_dict, self.db_json = load_vanilla_database_json(config.db_path)
        self.decks = load_tournament_decks(self.db_dict, config.deck_dir)

    def choose_matchup(self, rng: random.Random) -> tuple[dict[str, Any], dict[str, Any]]:
        if self.config.mirror_matches:
            deck = self.decks[0] if self.config.fixed_cycle_seed else rng.choice(self.decks)
            return deck, deck
        if self.config.fixed_cycle_seed:
            return self.decks[0], self.decks[0]
        return rng.choice(self.decks), rng.choice(self.decks)

    def generate_games(self, checkpoint_path: Path, cycle_seed: int) -> tuple[list[tuple[Any, ...]], list[SelfPlayStats]]:
        worker_count = max(1, min(self.config.workers, self.config.games_per_cycle))
        worker_args = {
            "db_json": self.db_json,
            "checkpoint_path": str(checkpoint_path),
            "model_config": asdict(self.model_config),
            "device": self.config.resolved_device(),
            "sims_per_move": self.config.sims_per_move,
            "mcts_batch_size": self.config.mcts_batch_size,
            "max_turns": self.config.max_turns,
            "max_moves": self.config.max_moves,
            "exploration_turns": self.config.exploration_turns,
            "temperature": self.config.temperature,
            "teacher_mix": self.config.teacher_mix,
            "dirichlet_alpha": self.config.root_dirichlet_alpha,
            "dirichlet_eps": self.config.root_dirichlet_eps,
            "mcts_only_selfplay": self.config.mcts_only_selfplay,
        }

        rng = random.Random(cycle_seed)
        tasks = []
        for game_idx in range(self.config.games_per_cycle):
            deck_a, deck_b = self.choose_matchup(rng)
            tasks.append((game_idx, cycle_seed + game_idx, deck_a, deck_b, worker_args))

        transitions: list[tuple[Any, ...]] = []
        stats: list[SelfPlayStats] = []
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=worker_count,
            initializer=_init_self_play_worker,
            initargs=(worker_args,),
        ) as executor:
            futures = [executor.submit(_play_self_play_game, *task) for task in tasks]
            for future in concurrent.futures.as_completed(futures):
                game_transitions, game_stats = future.result()
                transitions.extend(game_transitions)
                stats.append(SelfPlayStats(**game_stats))
        return transitions, stats


def _init_self_play_worker(worker_args: dict[str, Any]) -> None:
    """Initialize worker process: load model, database, and neural evaluator (one-time setup).
    
    WORKER LIFECYCLE:
      - Called once per worker process at startup (ProcessPoolExecutor initializer)
      - Loads model checkpoint (latest.pt) into worker's private memory
      - Creates game database (engine_rust.PyCardDatabase)
      - Instantiates neural evaluator for MCTS (search_mcts_alphazero)
    
    GLOBAL STATE (per worker):
      - _WORKER_DB: Shared card database (read-only after init)
      - _WORKER_MODEL: Neural network model (read-only, no gradients)
      - _WORKER_EVALUATOR: PyAlphaZeroEvaluator for MCTS inference
      - _WORKER_CONFIG: Config dict (sims_per_move, temperature, etc.)
    
    AUTO-SAVE CONSIDERATION:
      - Worker loads from checkpoint_path (latest.pt)
      - Each worker is independent; updates to latest.pt between game starts don't affect running games
      - At cycle end, new latest.pt is saved; next cycle's workers load new version
    
    Args:
      worker_args: Dict with db_json, checkpoint_path, model_config, sims_per_move, etc.
    """
    global _WORKER_DB, _WORKER_MODEL, _WORKER_EVALUATOR, _WORKER_CONFIG, _WORKER_DEVICE, _WORKER_CARD_LOOKUP

    torch.set_num_threads(1)
    _WORKER_CONFIG = worker_args
    _WORKER_DEVICE = torch.device(worker_args["device"])
    _configure_torch_runtime(_WORKER_DEVICE)
    _WORKER_DB = engine_rust.PyCardDatabase(worker_args["db_json"])
    _WORKER_CARD_LOOKUP = build_card_feature_lookup(json.loads(worker_args["db_json"]))

    model_config = VanillaTransformerConfig(**worker_args["model_config"])
    model = VanillaPolicyModel(model_config).to(_WORKER_DEVICE)
    checkpoint_path = Path(worker_args["checkpoint_path"])
    if checkpoint_path.exists():
        checkpoint = torch.load(checkpoint_path, map_location=_WORKER_DEVICE)
        _load_checkpoint_into_model(model, checkpoint)
    model.eval()
    _WORKER_MODEL = model
    if hasattr(engine_rust, "PyAlphaZeroEvaluator") and hasattr(engine_rust, "AlphaZeroTensorType"):
        _WORKER_EVALUATOR = engine_rust.PyAlphaZeroEvaluator(model, engine_rust.AlphaZeroTensorType.Vanilla)
    else:
        _WORKER_EVALUATOR = None


def _choose_action_from_policy(
    dense_policy: np.ndarray,
    mapping: dict[int, int],
    phase: int,
    turn: int,
    rng: random.Random,
) -> int:
    """Select action from policy distribution with temperature-based exploration.
    
    TEMPERATURE LOGIC:
      - exploration_turns=4: First 4 turns use temperature > 0 (sample from policy)
      - Later turns use temperature=0 (greedy, pick max probability)
      - Rationale: Early game discovery keeps training diverse, late game commits to best actions
    
    ACTION SELECTION:
      1. Extract valid action IDs (non-zero probability)
      2. If temperature > 0.01 (early game):
         - Normalize probabilities (sum=1)
         - Sample from distribution using policy as weights
         - Result: more exploration, less greedy
      3. Else (late game):
         - Pick greedy: highest probability action(s)
         - Ties broken by random choice (ensures reproducibility)
         - Result: deterministic best-response play
    
    POLICY ENCODING:
      dense_policy: 1D array with one entry per action in ACTION_SPACE
      Encoding: policy[i] = probability of action i (summed = 1.0 or 0 if no legal moves)
      mapping: dict[policy_id] → engine_action_id (converts encode format to game engine format)
    
    Args:
      dense_policy: Policy vector from model (normalized to sum=1)
      mapping: Policy ID → engine action ID conversion dict
      phase: Game phase (unused in current implementation)
      turn: Turn number in game (determines if temperature is active)
      rng: random.Random for sampling consistency
    
    Returns:
      Engine action ID to execute (maps back through mapping dict)
    """
    valid_ids = np.flatnonzero(dense_policy > 0)
    if len(valid_ids) == 0:
        return next(iter(mapping.values()))

    temperature = _WORKER_CONFIG["temperature"] if turn < _WORKER_CONFIG["exploration_turns"] else 0.0
    if temperature > 0.01:
        weights = dense_policy[valid_ids].astype(np.float64)
        weights = weights / weights.sum()
        chosen_policy_id = int(rng.choices(valid_ids.tolist(), weights=weights.tolist(), k=1)[0])
    else:
        best = float(np.max(dense_policy[valid_ids]))
        best_ids = valid_ids[dense_policy[valid_ids] >= best - 1e-8]
        chosen_policy_id = int(rng.choice(best_ids.tolist()))
    return mapping.get(chosen_policy_id, next(iter(mapping.values())))


def _apply_root_noise(policy: np.ndarray, legal_policy_ids: np.ndarray) -> np.ndarray:
    """Inject Dirichlet noise into root policy for exploration [AlphaGo Zero technique].
    
    DIRICHLET NOISE TECHNIQUE (prevents overfitting to same play patterns):
      Problem: Without noise, model might settle into deterministic openings
      Solution: Alpha-Go style Dirichlet noise on root action probabilities
      Effect: Encourages diversity across self-play games, prevents collapse
    
    ALGORITHM:
      1. Sample Dirichlet distribution: α = [dirichlet_alpha] * num_legal_actions
      2. Create noise vector with Dirichlet probabilities
      3. Blend: noisy_policy = (1 - ε) * original_policy + ε * noise
      4. Renormalize to sum=1
    
    HYPERPARAMETERS (from OvernightConfig):
      - root_dirichlet_alpha: Shape parameter (default 0.30)
        * Lower → noise more concentrated (less explosive)
        * Higher → noise more uniform (more exploration)
      - root_dirichlet_eps: Blend factor (default 0.20)
        * 0.0 = no noise (pure model)
        * 1.0 = pure noise (deterministic Dirichlet)
        * 0.20 = 20% noise, 80% model
    
    EXAMPLES:
      - legal_policy_ids=[0, 1, 2], original_policy=[0.7, 0.2, 0.1]
      - Noise=[0.25, 0.35, 0.40], blend 0.20:
      - Result: [0.70*(1-0.20) + 0.25*0.20, ...] = [0.61, 0.24, 0.15] ✓
    
    Args:
      policy: Current policy vector (shape: ACTION_SPACE)
      legal_policy_ids: Array of legal action indices (subset of ACTION_SPACE)
    
    Returns:
      Noisy policy (same shape as input, renormalized to sum=1)
      
    Side effect: Uses np.random (global state), seeded before self-play
    """
    if len(legal_policy_ids) <= 1:
        return policy
    noise = np.random.dirichlet([_WORKER_CONFIG["dirichlet_alpha"]] * len(legal_policy_ids)).astype(np.float32)
    updated = policy.copy()
    eps = float(_WORKER_CONFIG["dirichlet_eps"])
    updated[legal_policy_ids] = (1.0 - eps) * updated[legal_policy_ids] + eps * noise
    total = updated.sum()
    if total > 0:
        updated /= total
    return updated


def _get_suggestions(state) -> list[tuple[int, float, int]]:
    """Get MCTS move suggestions: preferring neural-guided MCTS (Phase 1 improvement).
    
    MCTS MODE SELECTION (smart fallback mechanism):
      NeuralMCTS (preferred):
        - Branch: if search_mcts_alphazero exists AND _WORKER_EVALUATOR available
        - Uses: PyAlphaZeroEvaluator for neural network policy priors + value estimates
        - Benefit: Stronger moves from learned neural guidance
        - Falls back if evaluator unavailable (legacy support)
      
      FallbackMCTS (legacy, if neural fails):
        - Uses: get_mcts_suggestions with basic UCB-based tree search
        - Reason: Backward compatibility if neural evaluator uninitialized
        - Performance: Weaker baseline, but still functional
    
    NEURAL MODE (Phase 1: Neural Evaluator Exposure):
      Arguments to search_mcts_alphazero:
        - sims_per_move: Depth of tree search (128 default)
        - _WORKER_EVALUATOR: PyAlphaZeroEvaluator wrapping the neural network
        - mcts_batch_size: Batch size for neural inference (128 default)
      
      Return format: [(action_id, value_estimate, visit_count), ...]
      - value_estimate: Neural network's value head prediction (-1 to 1 range)
      - visit_count: How many times this action visited during tree search
    
    Args: state - PyGameState from engine_rust
    
    Returns:
      List of (action_id, value, visit_count) tuples
      Sorted by visit count (most visited = most promising)
    """
    if hasattr(state, "search_mcts_alphazero"):
        if _WORKER_EVALUATOR is None:
            return []
        return state.search_mcts_alphazero(
            _WORKER_CONFIG["sims_per_move"],
            _WORKER_EVALUATOR,
            _WORKER_CONFIG["mcts_batch_size"],
        )
    return state.get_mcts_suggestions(
        _WORKER_CONFIG["sims_per_move"],
        1.41,
        engine_rust.SearchHorizon.GameEnd(),
        engine_rust.EvalMode.Normal,
    )


def _planner_policy_target(planner_sequence: Sequence[int] | None, mapping: dict[int, int]) -> np.ndarray | None:
    sequence = planner_sequence
    if not sequence:
        return None

    first_action = int(sequence[0])
    for policy_id, engine_action in mapping.items():
        if int(engine_action) == first_action:
            teacher = np.zeros(ACTION_SPACE, dtype=np.float32)
            teacher[int(policy_id)] = 1.0
            return teacher
    return None


def _planner_turn_sequence(state, phase: int) -> list[int] | None:
    if _WORKER_DB is None:
        return None

    action_ids: Sequence[int] | None = None
    try:
        if phase == PHASE_MAIN and hasattr(state, "plan_full_turn"):
            _score, planner_actions, _nodes, _breakdown = state.plan_full_turn(_WORKER_DB)
            action_ids = [int(action_id) for action_id in planner_actions]
            if not action_ids:
                return None

            sim_state = engine_rust.PyGameState(_WORKER_DB)
            sim_state.apply_state_json(state.to_json())
            for action_id in action_ids:
                legal_ids = set(int(legal_action) for legal_action in sim_state.get_legal_action_ids())
                if int(action_id) not in legal_ids:
                    return None
                sim_state.step(int(action_id))

            if int(sim_state.phase) == PHASE_LIVE_SET and hasattr(sim_state, "find_best_liveset_selection"):
                liveset_actions, _nodes, _score = sim_state.find_best_liveset_selection(_WORKER_DB)
                action_ids = list(action_ids) + [int(action_id) for action_id in liveset_actions]
        elif phase == PHASE_LIVE_SET and hasattr(state, "find_best_liveset_selection"):
            planner_actions, _nodes, _score = state.find_best_liveset_selection(_WORKER_DB)
            action_ids = [int(action_id) for action_id in planner_actions]
    except Exception:
        return None

    if not action_ids:
        return None
    return [int(action_id) for action_id in action_ids]


def _predict_model_policy(obs: np.ndarray, mask: np.ndarray) -> np.ndarray:
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=_WORKER_DEVICE).unsqueeze(0)
    mask_t = torch.as_tensor(mask, dtype=torch.bool, device=_WORKER_DEVICE).unsqueeze(0)
    with torch.inference_mode():
        logits, _values = _WORKER_MODEL(obs_t, mask_t)
        policy = torch.softmax(logits, dim=1)[0].cpu().numpy().astype(np.float32)
    return policy


def _build_dense_policy(
    state,
    state_json: dict[str, Any],
    player_json: dict[str, Any],
    current_player: int,
    phase: int,
    initial_deck: Sequence[int],
    mask: np.ndarray,
    mapping: dict[int, int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[int] | None]:
    if _WORKER_CARD_LOOKUP is None:
        raise RuntimeError("Worker card lookup was not initialized")

    obs = build_vanilla_observation(state_json, current_player, initial_deck, _WORKER_CARD_LOOKUP)
    model_policy = _predict_model_policy(obs, mask)
    planner_sequence = None
    teacher_policy = None
    if not _WORKER_CONFIG.get("mcts_only_selfplay", False):
        planner_sequence = _planner_turn_sequence(state, phase)
        teacher_policy = _planner_policy_target(planner_sequence, mapping)

    if teacher_policy is None:
        suggestions = _get_suggestions(state)
        teacher_policy = sparse_policy_from_engine_visits(player_json, suggestions, initial_deck, phase)

    if teacher_policy.sum() > 0:
        target_policy = teacher_policy.copy()
        mix = float(np.clip(_WORKER_CONFIG["teacher_mix"], 0.0, 1.0))
        if mix >= 1.0:
            execution_policy = teacher_policy.copy()
        else:
            execution_policy = (1.0 - mix) * model_policy + mix * teacher_policy
    else:
        target_policy = model_policy.copy()
        execution_policy = model_policy.copy()

    target_policy *= mask.astype(np.float32)
    exec_policy = execution_policy * mask.astype(np.float32)

    target_total = float(target_policy.sum())
    if target_total <= 0.0:
        target_policy = mask.astype(np.float32)
        target_total = float(target_policy.sum())
    target_policy /= max(target_total, 1.0)

    exec_total = float(exec_policy.sum())
    if exec_total <= 0.0:
        exec_policy = target_policy.copy()
        exec_total = float(exec_policy.sum())
    exec_policy /= max(exec_total, 1.0)

    return obs, target_policy, exec_policy, planner_sequence


def _play_self_play_game(
    game_idx: int,
    game_seed: int,
    deck_a: dict[str, Any],
    deck_b: dict[str, Any],
    _worker_args: dict[str, Any],
) -> tuple[list[tuple[Any, ...]], dict[str, Any]]:
    rng = random.Random(game_seed)
    np.random.seed(game_seed & 0xFFFFFFFF)

    state = engine_rust.PyGameState(_WORKER_DB)
    state.initialize_game_with_seed(
        deck_a["initial_deck"],
        deck_b["initial_deck"],
        deck_a["energy"],
        deck_b["energy"],
        [],
        [],
        game_seed,
    )
    state.silent = True
    state.debug_mode = False

    history: list[dict[str, Any]] = []
    start = time.time()
    moves = 0
    decision_points = 0
    planner_guided_points = 0

    while not state.is_terminal() and state.turn <= _WORKER_CONFIG["max_turns"] and moves < _WORKER_CONFIG["max_moves"]:
        legal_ids = state.get_legal_action_ids()
        if not legal_ids:
            break

        state_json = json.loads(state.to_json())
        current_player = int(state.current_player)
        phase = int(state_json.get("phase", -4))
        initial_deck = deck_a["initial_deck"] if current_player == 0 else deck_b["initial_deck"]
        player_json = state_json["players"][current_player]

        mask = build_legal_policy_mask(state, current_player, initial_deck, phase, legal_ids)
        mapping = build_policy_engine_mapping(player_json, legal_ids, initial_deck, phase)
        if not mapping:
            fallback = int(rng.choice(legal_ids))
            state.step(fallback)
            state.auto_step(_WORKER_DB)
            moves += 1
            continue

        obs, target_policy, execution_policy, planner_sequence = _build_dense_policy(
            state,
            state_json,
            player_json,
            current_player,
            phase,
            initial_deck,
            mask,
            mapping,
        )
        decision_points += 1
        if planner_sequence:
            planner_guided_points += 1

        legal_policy_ids = np.flatnonzero(mask)
        if planner_sequence is None and (moves == 0 or state.turn < _WORKER_CONFIG["exploration_turns"]):
            execution_policy = _apply_root_noise(execution_policy, legal_policy_ids)

        history.append(
            {
                "obs": obs,
                "policy_target": target_policy,
                "player": current_player,
                "mask": mask,
                "turn": int(state.turn),
            }
        )

        execution_actions = planner_sequence
        if not execution_actions:
            execution_actions = [_choose_action_from_policy(execution_policy, mapping, phase, int(state.turn), rng)]

        for action in execution_actions:
            legal_now = set(int(legal_action) for legal_action in state.get_legal_action_ids())
            if int(action) not in legal_now:
                break
            state.step(int(action))
            state.auto_step(_WORKER_DB)
            moves += 1
            if state.is_terminal() or state.turn > _WORKER_CONFIG["max_turns"] or moves >= _WORKER_CONFIG["max_moves"]:
                break

    winner = int(state.get_winner())
    p0 = state.get_player(0)
    p1 = state.get_player(1)
    p0_success = len(p0.success_lives)
    p1_success = len(p1.success_lives)
    final_turn = int(state.turn)

    transitions: list[tuple[Any, ...]] = []
    for item in history:
        player = item["player"]
        opp = 1 - player
        my_success = p0_success if player == 0 else p1_success
        opp_success = p1_success if player == 0 else p0_success
        if winner == player:
            win_target = 1.0
        elif winner in (0, 1):
            win_target = 0.0
        else:
            win_target = 0.5
        margin_target = float(np.clip((my_success - opp_success) / 3.0, -1.0, 1.0))
        speed_scale = max(0.0, (float(_WORKER_CONFIG["max_turns"]) - final_turn) / max(1.0, float(_WORKER_CONFIG["max_turns"])))
        efficiency_target = speed_scale if winner == player else (-speed_scale if winner in (0, 1) else 0.0)
        targets = np.array([win_target, margin_target, efficiency_target], dtype=np.float32)
        sparse_policy = dense_to_sparse(item["policy_target"])
        legal_policy_ids = np.flatnonzero(item["mask"]).astype(np.uint16)
        transitions.append((item["obs"], sparse_policy, legal_policy_ids, targets))

    stats = {
        "deck_a": deck_a["name"],
        "deck_b": deck_b["name"],
        "winner": winner,
        "turns": final_turn,
        "moves": moves,
        "p0_success": p0_success,
        "p1_success": p1_success,
        "decision_points": decision_points,
        "planner_guided_points": planner_guided_points,
        "duration_secs": time.time() - start,
    }
    return transitions, stats


def save_checkpoint(
    checkpoint_path: Path,
    model: VanillaPolicyModel,
    trainer: ReplayTrainer,
    cycle: int,
    config: OvernightConfig,
) -> None:
    """Save training state to disk: model weights, optimizer state, cycle counter, config.
    
    AUTO-SAVE MECHANISM:
      - Called at end of each cycle (run_overnight loop)
      - Saves to latest.pt (default) and archival checkpoints (e.g., cycle_0050.pt)
      - Ensures training can resume from exact point if interrupted
    
    CHECKPOINT CONTENTS (PyTorch .pt file):
      - "model": state_dict() of neural network weights
      - "optimizer": Adam optimizer state (momentum, variance estimates)
      - "cycle": Current training cycle number (for resumption)
      - "model_config": VanillaTransformerConfig params (for reconstruction)
      - "overnight_config": OvernightConfig params (for reproducibility)
      - "saved_at": Float timestamp when checkpoint was saved
      - "parameter_count": Total learnable parameters in model
    
    USAGE IN PIPELINE:
      1. After each cycle: save_checkpoint(latest.pt, ...)
      2. Every N cycles: copy latest.pt → cycle_NNNN.pt (archival)
      3. On startup: load_or_create_model() reads latest.pt if exists
      4. Resume: Restores exact cycle, loads model weights and optimizer state
    
    Args:
      checkpoint_path: Where to save (typically latest.pt or cycle_0050.pt)
      model: VanillaPolicyModel with trained weights
      trainer: ReplayTrainer with optimizer state
      cycle: Current training cycle (0-indexed)
      config: OvernightConfig for reproducibility
    
    Returns: None (saves to checkpoint_path as side effect)
    
    Auto-save: Called synchronously after training, blocks until disk write completes
    """
    payload = {
        "model": model.state_dict(),
        "optimizer": trainer.optimizer.state_dict(),
        "cycle": cycle,
        "model_config": asdict(model.config),
        "overnight_config": asdict(config),
        "saved_at": time.time(),
        "parameter_count": model.parameter_count(),
    }
    torch.save(payload, checkpoint_path)


def load_or_create_model(config: OvernightConfig, device: torch.device) -> tuple[VanillaPolicyModel, Path, int]:
    """Load model from latest checkpoint or create new model if none exists.
    
    STARTUP LOGIC (auto-resume):
      1. Check if latest.pt exists in checkpoint_dir
      2. If EXISTS: load weights, optimizer state, cycle number → resume exact point
      3. If NOT: create new model from config.model_preset or model_budget_millions
      4. Return (model, latest_path, start_cycle) to caller
    
    CHECKPOINT RECOVERY:
      - latest.pt contains all necessary state: model_config, optimizer, cycle
      - Reconstructs exact training state for seamless resumption
      - Example: If interrupted at cycle 42, restart loads cycle 42 and continues from cycle 43
    
    MODEL SIZING:
      If config.model_preset == "budget":
        - Auto-scale model to fit model_budget_millions (e.g., 2.5 MB)
        - Typical 2.5 MB budget → ~450k parameters
      Else:
        - Use preset: "tiny" (50k), "small" (450k), "base" (2M), "large" (6M)
    
    Args:
      config: OvernightConfig with checkpoint_dir, model_preset or model_budget_millions
      device: torch.device (cuda or cpu) for model creation/loading
    
    Returns:
      (model, latest_path, start_cycle): Loaded/created model, checkpoint path, starting cycle
      start_cycle: 0 if new model, else resumed cycle number from checkpoint
    
    Auto-save: Checkpoint dir created if missing, latest.pt read (no write here)
    """
    checkpoint_dir = Path(config.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    latest_path = checkpoint_dir / "latest.pt"
    start_cycle = 0

    if latest_path.exists():
        if not config.resume:
            raise RuntimeError(
                f"Checkpoint already exists at {latest_path}. Pass --resume to continue or choose a new --checkpoint-dir."
            )
        checkpoint = torch.load(latest_path, map_location=device)
        model_config = VanillaTransformerConfig(**checkpoint["model_config"])
        model = VanillaPolicyModel(model_config).to(device)
        _load_checkpoint_into_model(model, checkpoint)
        start_cycle = int(checkpoint.get("cycle", 0))
        return model, latest_path, start_cycle

    if config.model_preset == "budget":
        model_config = choose_vanilla_config_for_budget(config.model_budget_millions)
    else:
        model_config = VanillaTransformerConfig.from_preset(config.model_preset)
    model = VanillaPolicyModel(model_config).to(device)
    return model, latest_path, start_cycle


def append_cycle_log(log_path: Path, summary: CycleSummary) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "cycle,games,decisive_games,avg_turns,decisive_avg_turns,avg_duration_secs,"
        "p0_success_avg,p1_success_avg,draw_rate,planner_guided_ratio,"
        "buffer_count,train_loss,policy_loss,value_loss\n"
    )
    if not log_path.exists():
        log_path.write_text(header, encoding="utf-8")
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(
            f"{summary.cycle},{summary.games},{summary.decisive_games},"
            f"{summary.avg_turns:.4f},{summary.decisive_avg_turns:.4f},{summary.avg_duration_secs:.4f},"
            f"{summary.p0_success_avg:.4f},{summary.p1_success_avg:.4f},"
            f"{summary.draw_rate:.4f},{summary.planner_guided_ratio:.4f},"
            f"{summary.buffer_count},{summary.train_loss:.6f},"
            f"{summary.policy_loss:.6f},{summary.value_loss:.6f}\n"
        )


def append_benchmark_log(log_path: Path, cycle: int, results: dict[str, tuple[int, int, int]]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    header = "cycle,random_wins,random_losses,random_draws,greedy_wins,greedy_losses,greedy_draws\n"
    if not log_path.exists():
        log_path.write_text(header, encoding="utf-8")
    random_result = results.get("random", (0, 0, 0))
    greedy_result = results.get("greedy", (0, 0, 0))
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(
            f"{cycle},{random_result[0]},{random_result[1]},{random_result[2]},"
            f"{greedy_result[0]},{greedy_result[1]},{greedy_result[2]}\n"
        )


def append_selfplay_log(log_path: Path, cycle: int, train_stats: dict[str, float], game_stats: SelfPlayGameStats) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    header = "cycle,winner,turns,p0_success,p1_success,decided,train_loss,policy_loss,value_loss\n"
    if not log_path.exists():
        log_path.write_text(header, encoding="utf-8")
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(
            f"{cycle},{game_stats.winner},{game_stats.turns},{game_stats.p0_success},"
            f"{game_stats.p1_success},{int(game_stats.decided)},"
            f"{train_stats['loss']:.6f},{train_stats['policy']:.6f},{train_stats['value']:.6f}\n"
        )


def _collect_oracle_trajectory(
    config: OvernightConfig,
    db,
    deck_a: dict[str, Any],
    deck_b: dict[str, Any],
    card_lookup: dict[int, dict[str, Any]],
) -> tuple[list[tuple[Any, ...]], int, int, int, int]:
    """Play one game with oracle (planner) policy targets.

    Returns (transitions, winner, p0_success, p1_success, turns).

    Key invariant: the policy target at every decision point comes from the
    planner (plan_full_turn / find_best_liveset_selection) or, when the planner
    has no opinion, from a uniform distribution over legal actions.  The neural
    model's own predictions are NEVER used as policy targets — that would create
    a circular training loop with no improvement signal.

    Execution is also teacher-forced: the planner's action sequence is applied
    to the game engine, so observations stay on the optimal trajectory rather than
    drifting into positions created by a weak random model.
    """
    state = engine_rust.PyGameState(db)
    state.initialize_game_with_seed(
        deck_a["initial_deck"],
        deck_b["initial_deck"],
        deck_a["energy"],
        deck_b["energy"],
        [],
        [],
        config.seed,
    )
    state.silent = True
    state.debug_mode = False
    _apply_deterministic_setup(state, db)

    # (obs, target_policy_dense, mask, current_player)
    raw: list[tuple[np.ndarray, np.ndarray, np.ndarray, int]] = []
    moves = 0

    while not state.is_terminal() and state.turn <= config.max_turns and moves < config.max_moves:
        legal_ids = state.get_legal_action_ids()
        if not legal_ids:
            state.auto_step(db)
            moves += 1
            continue

        state_json = json.loads(state.to_json())
        current_player = int(state.current_player)
        phase = int(state_json.get("phase", -4))
        initial_deck = deck_a["initial_deck"] if current_player == 0 else deck_b["initial_deck"]
        player_json = state_json["players"][current_player]
        mask = build_legal_policy_mask(state, current_player, initial_deck, phase, legal_ids)
        mapping = build_policy_engine_mapping(player_json, legal_ids, initial_deck, phase)

        if not mapping:
            state.step(int(legal_ids[0]))
            state.auto_step(db)
            moves += 1
            continue

        obs = build_vanilla_observation(state_json, current_player, initial_deck, card_lookup)

        # ------------------------------------------------------------------ #
        # Oracle: ask the planner which action(s) it recommends              #
        # ------------------------------------------------------------------ #
        oracle_actions: list[int] | None = None
        if phase == PHASE_MAIN and hasattr(state, "plan_full_turn"):
            try:
                _, planner_actions, _, _ = state.plan_full_turn(db)
                if planner_actions:
                    oracle_actions = [int(a) for a in planner_actions]
            except Exception:
                pass
        elif phase == PHASE_LIVE_SET and hasattr(state, "find_best_liveset_selection"):
            try:
                planner_actions, _, _ = state.find_best_liveset_selection(db)
                if planner_actions:
                    oracle_actions = [int(a) for a in planner_actions]
            except Exception:
                pass

        # ------------------------------------------------------------------ #
        # Build policy target from oracle (one-hot on first planner action)  #
        # Falls back to uniform legal — never to model-greedy.               #
        # ------------------------------------------------------------------ #
        target_policy = np.zeros(ACTION_SPACE, dtype=np.float32)
        if oracle_actions:
            first_action = oracle_actions[0]
            for pid, eng_act in mapping.items():
                if int(eng_act) == first_action:
                    target_policy[int(pid)] = 1.0
                    break

        if target_policy.sum() <= 0.0:
            # Honest uniform: we don't know the best action, so don't pretend we do.
            legal_float = mask.astype(np.float32)
            total = legal_float.sum()
            if total > 0:
                target_policy = legal_float / total

        raw.append((obs, target_policy, mask, current_player))

        # ------------------------------------------------------------------ #
        # Execute: follow oracle sequence (teacher-forced) so later          #
        # observations stay on the intended optimal game trajectory.          #
        # ------------------------------------------------------------------ #
        if oracle_actions:
            for action in oracle_actions:
                legal_now = {int(a) for a in state.get_legal_action_ids()}
                if int(action) not in legal_now:
                    break
                state.step(int(action))
                state.auto_step(db)
                moves += 1
                if state.is_terminal():
                    break
        else:
            # No oracle guidance: deterministic fallback (first legal mapped action).
            action = next(iter(mapping.values()))
            state.step(int(action))
            state.auto_step(db)
            moves += 1

    winner = int(state.get_winner())
    p0 = state.get_player(0)
    p1 = state.get_player(1)
    p0_success = len(p0.success_lives)
    p1_success = len(p1.success_lives)
    final_turn = int(state.turn)

    # Retrospectively label value targets now that we know the outcome.
    transitions: list[tuple[Any, ...]] = []
    for obs, target_policy, mask, player in raw:
        my_success = p0_success if player == 0 else p1_success
        opp_success = p1_success if player == 0 else p0_success
        if winner == player:
            win_target = 1.0
        elif winner in (0, 1):
            win_target = 0.0
        else:
            win_target = 0.5
        margin_target = float(np.clip((my_success - opp_success) / 3.0, -1.0, 1.0))
        speed_scale = max(0.0, (float(config.max_turns) - final_turn) / max(1.0, float(config.max_turns)))
        efficiency_target = speed_scale if winner == player else (-speed_scale if winner in (0, 1) else 0.0)
        targets = np.array([win_target, margin_target, efficiency_target], dtype=np.float32)
        transitions.append((
            obs,
            dense_to_sparse(target_policy),
            targets,
            np.flatnonzero(mask).astype(np.uint16),
        ))

    return transitions, winner, p0_success, p1_success, final_turn


def run_overfit_single_game(config: OvernightConfig) -> None:
    """Overfit mode: pure supervised learning from a single oracle game.

    The network is trained to reproduce the planner's *optimal* action sequence
    for one deterministic game (fixed seed + fixed deck mirror match).  Because
    every policy target is derived from the planner — never from the model's own
    predictions — the policy head receives a genuine learning signal from cycle 1.

    Convergence metric: oracle_match_rate — the fraction of decision points where
    the model's greedy argmax equals the planner's recommended action.  Logged to
    overfit_log.csv each cycle; training stops early once the rate reaches 99 %.
    """
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    _prepare_run_paths(config)
    _assert_run_paths_ready(config)

    device = _torch_device(config.resolved_device())
    _configure_torch_runtime(device)
    model, latest_path, start_cycle = load_or_create_model(config, device)
    trainer = ReplayTrainer(config, model, device)
    buffer = PersistentBuffer(
        config.buffer_dir,
        max(config.buffer_size, 4096),
        OBS_DIM,
        ACTION_SPACE,
        sparse_limit=config.sparse_limit,
    )

    full_db, db_json = load_vanilla_database_json(config.db_path)
    card_lookup = build_card_feature_lookup(full_db)
    decks = load_tournament_decks(full_db, config.deck_dir)
    deck = decks[0]
    db = engine_rust.PyCardDatabase(db_json)

    print(json.dumps({
        "run_name": config.run_name,
        "mode": "overfit",
        "device": str(device),
        "model": model.describe(),
        "deck": deck["name"],
        "seed": config.seed,
    }, indent=2))

    # Generate oracle trajectory once — deterministic for fixed seed + fixed deck.
    oracle_transitions, oracle_winner, oracle_p0, oracle_p1, oracle_turns = _collect_oracle_trajectory(
        config, db, deck, deck, card_lookup
    )
    if not oracle_transitions:
        raise RuntimeError(
            "Oracle trajectory is empty — the game ended immediately or the planner has no "
            "actions.  Check that the deck is valid and the engine initialises correctly."
        )
    print(
        f"[ORACLE] {len(oracle_transitions)} decision points | "
        f"winner={oracle_winner} p0_success={oracle_p0} p1_success={oracle_p1} turns={oracle_turns}",
        flush=True,
    )

    overfit_log_path = Path(config.checkpoint_dir) / "overfit_log.csv"
    if not overfit_log_path.exists():
        overfit_log_path.parent.mkdir(parents=True, exist_ok=True)
        overfit_log_path.write_text(
            "cycle,oracle_match_rate,loss,policy_loss,value_loss\n", encoding="utf-8"
        )

    cycle = start_cycle
    while cycle < start_cycle + config.cycles:
        cycle += 1

        # Replace buffer with fresh oracle data each cycle — never train on stale
        # transitions from earlier (weaker) policies.
        buffer.ptr = 0
        buffer.count = 0
        buffer._save_meta()
        for obs, sparse_policy, targets, mask_indices in oracle_transitions:
            buffer.add(obs, sparse_policy, targets, mask_indices)
        buffer.flush()

        train_stats = trainer.train_steps(buffer, config.train_steps_per_cycle)
        save_checkpoint(latest_path, model, trainer, cycle, config)
        if cycle % config.checkpoint_every_cycles == 0:
            archival = Path(config.checkpoint_dir) / f"cycle_{cycle:05d}.pt"
            save_checkpoint(archival, model, trainer, cycle, config)

        # ------------------------------------------------------------------ #
        # Oracle match rate: batched inference over all oracle positions.     #
        # Measures what fraction of the model's greedy choices agree with     #
        # the planner — the primary convergence indicator.                    #
        # ------------------------------------------------------------------ #
        model.eval()
        n = len(oracle_transitions)
        obs_batch = np.stack([t[0] for t in oracle_transitions])
        mask_batch = np.zeros((n, ACTION_SPACE), dtype=bool)
        for i, (_, _, _, mask_indices) in enumerate(oracle_transitions):
            mask_batch[i, mask_indices] = True
        obs_t = torch.as_tensor(obs_batch, dtype=torch.float32).to(device)
        mask_t = torch.as_tensor(mask_batch, dtype=torch.bool).to(device)
        with torch.inference_mode():
            logits_batch, _ = model(obs_t, mask_t)
        logits_np = logits_batch.cpu().numpy()
        model.train()

        matches = 0
        for i, (_, sparse_policy, _, mask_indices) in enumerate(oracle_transitions):
            p_indices, p_values = sparse_policy
            target_dense = np.zeros(ACTION_SPACE, dtype=np.float32)
            target_dense[p_indices.astype(np.int32)] = p_values.astype(np.float32)
            oracle_action = int(np.argmax(target_dense))
            if target_dense[oracle_action] <= 0.0:
                continue
            legal_logits = logits_np[i].copy()
            legal_logits[~mask_batch[i]] = -1e9
            if int(np.argmax(legal_logits)) == oracle_action:
                matches += 1

        oracle_match = matches / max(n, 1)

        with open(str(overfit_log_path), "a", encoding="utf-8") as fh:
            fh.write(
                f"{cycle},{oracle_match:.4f},"
                f"{train_stats['loss']:.6f},{train_stats['policy']:.6f},{train_stats['value']:.6f}\n"
            )
        print(
            f"[OVERFIT {cycle}] oracle_match={oracle_match:.1%} "
            f"loss={train_stats['loss']:.4f} policy={train_stats['policy']:.4f} "
            f"value={train_stats['value']:.4f} positions={n}",
            flush=True,
        )

        if oracle_match >= 0.99:
            print(
                f"[OVERFIT] Converged at cycle {cycle} (oracle_match={oracle_match:.1%}) — stopping.",
                flush=True,
            )
            break


def _choose_model_action(
    state,
    state_json: dict[str, Any],
    current_player: int,
    initial_deck: Sequence[int],
    legal_ids: Sequence[int],
    model: VanillaPolicyModel,
    device: torch.device,
    card_lookup: dict[int, dict[str, Any]],
) -> int:
    phase = int(state_json.get("phase", -4))
    player_json = state_json["players"][current_player]
    mask = build_legal_policy_mask(state, current_player, initial_deck, phase, legal_ids)
    mapping = build_policy_engine_mapping(player_json, legal_ids, initial_deck, phase)
    if not mapping:
        return int(legal_ids[0])

    obs = build_vanilla_observation(state_json, current_player, initial_deck, card_lookup)
    obs_t = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0).to(device)
    mask_t = torch.as_tensor(mask, dtype=torch.bool).unsqueeze(0).to(device)

    with torch.inference_mode():
        logits, _ = model(obs_t, mask_t)
        policy = torch.softmax(logits, dim=1)[0].cpu().numpy().astype(np.float32)

    policy_ids = np.asarray(list(mapping.keys()), dtype=np.int64)
    legal_policy = policy[policy_ids]
    best_id = int(policy_ids[int(np.argmax(legal_policy))]) if len(policy_ids) else ACTION_SPACE - 1
    return int(mapping.get(best_id, legal_ids[0]))


def _apply_deterministic_setup(state, db) -> None:
    setup_steps = 0
    while state.phase < 1 and setup_steps < 200:
        legal_ids = state.get_legal_action_ids()
        if not legal_ids:
            break

        if state.phase == -3:
            if 20000 in legal_ids:
                action = 20000
            elif 21002 in legal_ids:
                action = 21002
            else:
                action = int(legal_ids[0])
        elif state.phase == -2:
            action = 5000 if 5000 in legal_ids else int(legal_ids[0])
        else:
            action = 0 if 0 in legal_ids else int(legal_ids[0])

        state.step(action)
        state.auto_step(db)
        setup_steps += 1


def _play_benchmark_game(
    model: VanillaPolicyModel,
    opponent_type: str,
    model_as_player0: bool,
    deck_p0: dict[str, Any],
    deck_p1: dict[str, Any],
    config: OvernightConfig,
    db,
    device: torch.device,
    seed: int,
    card_lookup: dict[int, dict[str, Any]],
) -> int:
    state = engine_rust.PyGameState(db)
    state.initialize_game_with_seed(
        deck_p0["initial_deck"],
        deck_p1["initial_deck"],
        deck_p0["energy"],
        deck_p1["energy"],
        [],
        [],
        seed,
    )
    state.silent = True
    state.debug_mode = False
    _apply_deterministic_setup(state, db)

    rng = random.Random(seed)
    moves = 0
    while not state.is_terminal() and state.turn <= config.max_turns and moves < config.max_moves:
        current_player = int(getattr(state, "acting_player", state.current_player))
        legal_ids = state.get_legal_action_ids()
        if not legal_ids:
            state.auto_step(db)
            moves += 1
            continue

        state_json = json.loads(state.to_json())
        is_model_turn = (current_player == 0) if model_as_player0 else (current_player == 1)
        if is_model_turn:
            initial_deck = deck_p0["initial_deck"] if current_player == 0 else deck_p1["initial_deck"]
            action = _choose_model_action(state, state_json, current_player, initial_deck, legal_ids, model, device, card_lookup)
        elif opponent_type == "greedy":
            action = int(state.get_greedy_action(db, current_player, 0))
        else:
            action = int(rng.choice(legal_ids))

        try:
            state.step(action)
            state.auto_step(db)
        except Exception:
            return 2
        moves += 1

    winner = int(state.get_winner())
    if winner not in (0, 1):
        return 2
    return winner if model_as_player0 else (1 - winner)


def run_benchmark_suite(
    current_model: VanillaPolicyModel,
    config: OvernightConfig,
    device: torch.device,
    seed: int,
) -> dict[str, tuple[int, int, int]]:
    if config.benchmark_every_cycles <= 0 or config.benchmark_games <= 0:
        return {}

    _configure_torch_runtime(device)
    full_db, db_json = load_vanilla_database_json(config.db_path)
    card_lookup = build_card_feature_lookup(full_db)
    decks = load_tournament_decks(full_db, config.deck_dir)
    if len(decks) < 2:
        return {}

    db = engine_rust.PyCardDatabase(db_json)
    current_model.eval()
    benchmark_seed = config.seed if config.fixed_cycle_seed else seed
    rng = random.Random(benchmark_seed + 424242)
    results: dict[str, tuple[int, int, int]] = {}

    for opponent_type in ("random", "greedy"):
        wins = 0
        losses = 0
        draws = 0
        for game_idx in range(config.benchmark_games):
            if config.fixed_cycle_seed:
                deck_a = decks[0]
                deck_b = decks[0]
            else:
                deck_a = rng.choice(decks)
                deck_b = rng.choice(decks)
            model_as_player0 = (game_idx % 2) == 0
            winner = _play_benchmark_game(
                current_model,
                opponent_type,
                model_as_player0,
                deck_a if model_as_player0 else deck_b,
                deck_b if model_as_player0 else deck_a,
                config,
                db,
                device,
                benchmark_seed + game_idx,
                card_lookup,
            )
            if winner == 0:
                wins += 1
            elif winner == 1:
                losses += 1
            else:
                draws += 1
        results[opponent_type] = (wins, losses, draws)

    return results


def run_overnight(config: OvernightConfig) -> None:
    """Main orchestration loop: alternates between self-play generation, training, and arena evaluation.
    
    LOOP STRUCTURE (per cycle):
      1. Generate games: Run config.games_per_cycle games in parallel across config.workers
      2. Store transitions: Write all game experiences to disk-backed replay buffer
      3. Train network: Run config.train_steps_per_cycle gradient descent steps
      4. Save checkpoint: Save latest model to disk
      5. [Optional] Arena evaluation: Every config.arena_every_cycles, validate improvement
      6. Log cycle statistics: Games, decisive%, avg turns, loss metrics
    
    TERMINATION CONDITIONS:
      - Completes all config.cycles training cycles, OR
      - Hits config.max_hours wall-clock timeout
    
    CHECKPOINTS SAVED:
      - latest_model.pt: Always points to most recent checkpoint (autosaves every cycle)
      - cycle_XXXXX.pt: Archival checkpoints saved every config.checkpoint_every_cycles
      - best_model.pt: Tracks best model per arena evaluation (only updated at improvement)
    
    ARENA EVALUATION:
      - Fixed deck pairs (8 pairs × 2 reversals = 16 games) prevent matchup luck
      - Requires win_rate >= threshold on decisive games
      - Only promotes if statistically significant (e.g., 9+ wins at 55% threshold)
    """
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    _prepare_run_paths(config)
    _assert_run_paths_ready(config)

    device = _torch_device(config.resolved_device())
    _configure_torch_runtime(device)
    model, latest_path, start_cycle = load_or_create_model(config, device)
    trainer = ReplayTrainer(config, model, device)
    coordinator = SelfPlayCoordinator(config, model.config)
    buffer = PersistentBuffer(config.buffer_dir, config.buffer_size, OBS_DIM, ACTION_SPACE, sparse_limit=config.sparse_limit)

    # Setup best model tracking for arena
    best_model_path = Path(config.checkpoint_dir) / "best_model.pt"
    if not best_model_path.exists():
        save_checkpoint(best_model_path, model, trainer, start_cycle, config)

    print(json.dumps({
        "run_name": config.run_name,
        "device": str(device),
        "model": model.describe(),
        "games_per_cycle": config.games_per_cycle,
        "workers": config.workers,
        "sims_per_move": config.sims_per_move,
        "train_steps_per_cycle": config.train_steps_per_cycle,
        "buffer_dir": str(config.buffer_dir),
        "checkpoint_dir": str(config.checkpoint_dir),
        "arena_size": config.arena_size,
        "arena_enabled": config.arena_size > 0,
        "fixed_cycle_seed": config.fixed_cycle_seed,
        "freeze_selfplay_after_cycle_one": config.freeze_selfplay_after_cycle_one,
        "mcts_only_selfplay": config.mcts_only_selfplay,
    }, indent=2))

    deadline = time.time() + config.max_hours * 3600.0 if config.max_hours > 0 else None
    cycle = start_cycle
    while cycle < start_cycle + config.cycles:
        if deadline is not None and time.time() >= deadline:
            break
        cycle += 1
        cycle_started_at = time.time()
        checkpoint_for_workers = latest_path
        if not checkpoint_for_workers.exists():
            save_checkpoint(checkpoint_for_workers, model, trainer, cycle - 1, config)

        cycle_seed = config.seed if config.fixed_cycle_seed else config.seed + cycle * 10_000
        if config.freeze_selfplay_after_cycle_one and cycle > start_cycle + 1:
            stats = []
        else:
            transitions, stats = coordinator.generate_games(checkpoint_for_workers, cycle_seed)
            for obs, sparse_policy, mask_indices, targets in transitions:
                buffer.add(obs, sparse_policy, targets, mask_indices)
            buffer.flush()

        if buffer.count < max(config.batch_size, config.min_buffer_samples):
            train_stats = _zero_train_stats()
        else:
            train_stats = trainer.train_steps(buffer, config.train_steps_per_cycle)
        save_checkpoint(latest_path, model, trainer, cycle, config)
        if cycle % config.checkpoint_every_cycles == 0:
            archival = Path(config.checkpoint_dir) / f"cycle_{cycle:05d}.pt"
            save_checkpoint(archival, model, trainer, cycle, config)

        # Arena evaluation every N cycles (fixed deck matchups, controlled for luck)
        if config.arena_size > 0 and cycle % config.arena_every_cycles == 0:
            arena_wins, arena_losses, arena_draws = run_arena(
                model, best_model_path, config, device, cycle_seed
            )
            total_decisive = arena_wins + arena_losses
            win_rate = arena_wins / total_decisive if total_decisive > 0 else 0.5
            is_significant = _is_statistically_significant(arena_wins, arena_losses, arena_draws, config.arena_win_threshold)
            
            if is_significant and win_rate >= config.arena_win_threshold:
                save_checkpoint(best_model_path, model, trainer, cycle, config)
                print(f"[ARENA] ✓ New best model! Win: {arena_wins}/{total_decisive} ({win_rate:.1%}) [draws: {arena_draws}]")
            else:
                status = "insufficient" if not is_significant else f"{win_rate:.1%}"
                print(f"[ARENA] ✗ Not promoted. Win: {arena_wins}/{total_decisive} ({status}) [draws: {arena_draws}]")

        decisive = sum(1 for entry in stats if entry.winner in (0, 1))
        avg_turns = float(np.mean([entry.turns for entry in stats])) if stats else 0.0
        decisive_turns = [entry.turns for entry in stats if entry.winner in (0, 1)]
        decisive_avg_turns = float(np.mean(decisive_turns)) if decisive_turns else 0.0
        avg_duration = float(np.mean([entry.duration_secs for entry in stats])) if stats else 0.0
        avg_p0_success = float(np.mean([entry.p0_success for entry in stats])) if stats else 0.0
        avg_p1_success = float(np.mean([entry.p1_success for entry in stats])) if stats else 0.0
        total_decision_points = sum(entry.decision_points for entry in stats)
        planner_guided_ratio = (
            sum(entry.planner_guided_points for entry in stats) / total_decision_points
            if total_decision_points > 0
            else 0.0
        )
        summary = CycleSummary(
            cycle=cycle,
            games=len(stats),
            decisive_games=decisive,
            avg_turns=avg_turns,
            decisive_avg_turns=decisive_avg_turns,
            avg_duration_secs=avg_duration,
            p0_success_avg=avg_p0_success,
            p1_success_avg=avg_p1_success,
            draw_rate=(1.0 - (decisive / len(stats))) if stats else 0.0,
            planner_guided_ratio=planner_guided_ratio,
            buffer_count=buffer.count,
            train_loss=train_stats["loss"],
            policy_loss=train_stats["policy"],
            value_loss=train_stats["value"],
        )
        append_cycle_log(Path(config.checkpoint_dir) / "overnight_log.csv", summary)
        if config.benchmark_every_cycles > 0 and cycle % config.benchmark_every_cycles == 0:
            benchmark_results = run_benchmark_suite(model, config, device, cycle_seed)
            if benchmark_results:
                append_benchmark_log(Path(config.checkpoint_dir) / "benchmark_log.csv", cycle, benchmark_results)
                random_result = benchmark_results.get("random", (0, 0, 0))
                greedy_result = benchmark_results.get("greedy", (0, 0, 0))
                print(
                    f"[BENCH] random={random_result[0]}-{random_result[1]}-{random_result[2]} "
                    f"greedy={greedy_result[0]}-{greedy_result[1]}-{greedy_result[2]}",
                    flush=True,
                )
        _print_cycle_summary(summary, time.time() - cycle_started_at)


def run_arena(
    current_model: VanillaPolicyModel,
    best_model_path: Path,
    config: OvernightConfig,
    device: torch.device,
    seed: int,
) -> tuple[int, int, int]:
    """Arena evaluation: tournament between current model vs best model with fixed deck matchups.
    
    DESIGN RATIONALE (deck luck control):
      PROBLEM: Random deck selection per game confounds model quality with matchup luck
        - If you pick random decks each game, 16 games = 16 different random matchups
        - Weak model might win by luck if it happens to draw good matchups
        - Strong model might lose by luck if it draws bad matchups
        - Variance = HUGE, makes promotion decisions unreliable
      
      SOLUTION: Pre-select FIXED deck pairs, reuse them for all games
        - Select 8 deck pairs deterministically (seeded RNG, reproducible)
        - Play each pair twice: forward + reversed player order
        - All 16 games use same matchups, only model strength varies
        - Variance = controlled, promotion decisions reliable
    
    GAME STRUCTURE (for arena_size=16 → 8 pairs):
      1. Load tournament deck pool from config.deck_dir
      2. Deterministically select 8 pairs via seeded RNG (reproducible across runs)
      3. For each pair (deck_a, deck_b):
         * Game 1: current_model=Player0, best_model=Player1 with (deck_a, deck_b)
         * Game 2: best_model=Player0, current_model=Player1 with (deck_b, deck_a) [reversed]
      4. Track wins, losses, draws from current_model's perspective
    
    OUTPUTS & AUTO-SAVE:
      - Returns (wins, losses, draws) for caller's statistical evaluation
      - Caller decides promotion based on _is_statistically_significant() check
      - If promoted: caller saves current_model → best_model.pt (auto-persists to disk)
      - Checkpoint directory: uses config.checkpoint_dir for persistence
    
    Args:
      current_model: New model to evaluate
      best_model_path: Path to saved best_model from previous cycles (auto-loaded here)
      config: OvernightConfig with arena_size, deck_dir, device settings
      device: torch.device (cuda or cpu) for inference
      seed: Training cycle seed (base for deterministic arena seed = seed + 99999)
    
    Returns:
      (wins, losses, draws): Current model's game record vs best model
      Example: (9, 5, 2) = current won 9, best won 5, 2 draws
      
    Note: Only decisive games count in statistical significance check (draws ignored).
    """
    if not best_model_path.exists():
        return 0, 0, 0

    _configure_torch_runtime(device)
    
    # Load best model
    best_checkpoint = torch.load(best_model_path, map_location=device)
    best_model = VanillaPolicyModel(current_model.config).to(device)
    _load_checkpoint_into_model(best_model, best_checkpoint)
    best_model.eval()
    current_model.eval()
    
    # Load decks and create fixed matchup pairs
    full_db, db_json = load_vanilla_database_json(config.db_path)
    card_lookup = build_card_feature_lookup(full_db)
    all_decks = load_tournament_decks(full_db, config.deck_dir)
    if len(all_decks) < 2:
        return 0, 0, 0
    
    arena_seed = seed + 99999
    rng = random.Random(arena_seed)
    
    # Deterministically select fixed deck pairs for this arena
    num_pairs = max(1, config.arena_size // 2)
    selected_decks = rng.sample(all_decks, min(len(all_decks), num_pairs * 2))
    deck_pairs = [(selected_decks[i], selected_decks[i+1]) for i in range(0, len(selected_decks)-1, 2)]
    
    wins, losses, draws = 0, 0, 0
    game_idx = 0
    
    # Play each deck pair twice: once as (deck_a, deck_b), once reversed
    for deck_a, deck_b in deck_pairs:
        if game_idx >= config.arena_size:
            break
        
        # Game 1: current=P0, best=P1
        winner = _play_arena_game(
            current_model, best_model, deck_a, deck_b, config, device, arena_seed + game_idx, db_json, card_lookup
        )
        if winner == 0:
            wins += 1
        elif winner == 1:
            losses += 1
        else:
            draws += 1
        game_idx += 1
        
        if game_idx >= config.arena_size:
            break
        
        # Game 2 (reversed): current=P1, best=P0
        winner = _play_arena_game(
            best_model, current_model, deck_b, deck_a, config, device, arena_seed + game_idx, db_json, card_lookup
        )
        # Note: winner is from best_model perspective, so flip for current_model
        if winner == 1:
            wins += 1
        elif winner == 0:
            losses += 1
        else:
            draws += 1
        game_idx += 1
    
    return wins, losses, draws


def _play_arena_game(
    model_p0: VanillaPolicyModel,
    model_p1: VanillaPolicyModel,
    deck_p0: dict[str, Any],
    deck_p1: dict[str, Any],
    config: OvernightConfig,
    device: torch.device,
    seed: int,
    db_json: str,
    card_lookup: dict[int, dict[str, Any]],
) -> int:
    """Play a single arena game between two models with fixed decks.
    
    Each turn:
      1. Get game observation (state.to_vanilla_tensor())
      2. Pass through model to get policy logits
      3. Apply softmax to convert logits → probability distribution
      4. Filter to legal actions only (set illegal actions to 0)
      5. Select greedy action (highest legal probability)
      6. Execute step in game engine
    
    DESIGN NOTE (greedy action selection):
      Unlike self-play (which samples with temperature), arena uses greedy deterministic play.
      This ensures consistent evaluation: model quality difference drives winner, not randomness.
    
    ERROR HANDLING:
      - If step() fails (malformed action): return 2 (draw, neutral outcome)
      - Infinite loops prevented: max_turns limit (typically 10)
    
    Args:
    model_p0, model_p1: Neural network models for players 0 and 1
    deck_p0, deck_p1: Fixed tournament decks from load_tournament_decks()
      config: Configuration with db_path, max_turns
      device: torch.device (cuda or cpu)
      seed: Unused in deterministic arena (kept for consistency, could seed RNG for tie-breaking)
    
    Returns:
      0: Player 0 (model_p0) won the game
      1: Player 1 (model_p1) won the game
      2: Draw (if terminal condition or error reached max turns)
    """
    db = engine_rust.PyCardDatabase(db_json)
    
    state = engine_rust.PyGameState(db)
    state.initialize_game_with_seed(
        deck_p0["initial_deck"],
        deck_p1["initial_deck"],
        deck_p0["energy"],
        deck_p1["energy"],
        [],
        [],
        seed,
    )
    state.silent = True
    state.debug_mode = False

    phase_rps = -3
    phase_turn_choice = -2
    phase_mulligan_p1 = -1
    phase_mulligan_p2 = 0
    action_pass = 0
    action_turn_choice_first = 5000
    action_rps_rock_p1 = 20000
    action_rps_scissors_p2 = 21002

    setup_steps = 0
    while state.phase < 1 and setup_steps < 200:
        if state.phase == phase_rps:
            if state.rps_choices[0] == -1:
                state.step(action_rps_rock_p1)
            elif state.rps_choices[1] == -1:
                state.step(action_rps_scissors_p2)
        elif state.phase == phase_turn_choice:
            state.step(action_turn_choice_first)
        elif state.phase in (phase_mulligan_p1, phase_mulligan_p2):
            state.step(action_pass)
        else:
            state.step(action_pass)
        setup_steps += 1

    move_count = 0
    while not state.is_terminal() and state.turn <= config.max_turns and move_count < config.max_moves:
        current_player = int(getattr(state, "acting_player", state.current_player))
        model = model_p0 if current_player == 0 else model_p1
        legal_ids = state.get_legal_action_ids()
        if not legal_ids:
            state.auto_step(db)
            move_count += 1
            continue

        state_json = json.loads(state.to_json())
        phase = int(state_json.get("phase", -4))
        initial_deck = deck_p0["initial_deck"] if current_player == 0 else deck_p1["initial_deck"]
        player_json = state_json["players"][current_player]
        mask = build_legal_policy_mask(state, current_player, initial_deck, phase, legal_ids)
        mapping = build_policy_engine_mapping(player_json, legal_ids, initial_deck, phase)
        if not mapping:
            state.step(int(legal_ids[0]))
            state.auto_step(db)
            move_count += 1
            continue

        obs = build_vanilla_observation(state_json, current_player, initial_deck, card_lookup)
        obs_t = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0).to(device)
        mask_t = torch.as_tensor(mask, dtype=torch.bool).unsqueeze(0).to(device)

        with torch.inference_mode():
            logits, _ = model(obs_t, mask_t)
            policy = torch.softmax(logits, dim=1)[0].cpu().numpy().astype(np.float32)

        policy_ids = np.asarray(list(mapping.keys()), dtype=np.int64)
        legal_policy = policy[policy_ids]
        if legal_policy.sum() <= 0:
            action = next(iter(mapping.values()))
        else:
            best_id = int(policy_ids[int(np.argmax(legal_policy))])
            action = mapping[best_id]
        
        try:
            state.step(action)
            state.auto_step(db)
        except Exception:
            return 2
        
        move_count += 1
    
    winner = state.get_winner()
    return winner if winner in (0, 1) else 2


def _is_statistically_significant(wins: int, losses: int, draws: int, threshold: float = 0.55) -> bool:
    """Check if win rate is statistically significant above threshold on decisive games.
    
    RATIONALE (deck luck protection):
      In 16 games played by random agents: expect ~50% win rate by definition
      To prove model is actually stronger: need win rate clearly above 50%
      Threshold=0.55 means "at least 55% win rate on games that had a winner"
      
    DRAWS ARE IGNORED:
      Only wins + losses count (decisive games)
      Why? Draws don't measure strength (neither player won), just neutral outcome
      Example: wins=9, losses=5, draws=2 → win_rate = 9/(9+5) = 64.3%
      
    SETTING THE THRESHOLD:
      threshold=0.55 is conservative protection against short-term variance
      For arena_size=16 → 8 pairs → ~16 decisive games after removing draws
      Requires 9+ wins to pass (56.25% win rate)
      Gives buffer: if random fluctuation causes 1-2 upsets, still likely to pass
      
    EXAMPLE SCENARIOS (arena_size=16, threshold=0.55):
      wins=9, losses=5, draws=2 → rate=0.643 → PASS (clearly stronger)
      wins=8, losses=6, draws=2 → rate=0.571 → MARGINAL (weak pass if threshold=0.55)
      wins=7, losses=7, draws=2 → rate=0.500 → FAIL (no evidence of strength)
      wins=10, losses=4, draws=2 → rate=0.714 → STRONG PASS (high confidence)
    
    Args:
      wins: Number of games current model won vs best model
      losses: Number of games current model lost vs best model
      draws: Number of decisive games (ignored in calculation, only for logging)
      threshold: Minimum win rate required (default 0.55 = 55%)
    
    Returns:
      True if win_rate >= threshold on decisive games, False otherwise
      (False also returned if zero decisive games played)
    """
    total_decisive = wins + losses
    if total_decisive == 0:
        return False
    win_rate = wins / total_decisive
    # Require point estimate clearly above threshold
    return win_rate >= threshold


def run_selfplay_only(config: OvernightConfig) -> None:
    _assert_run_paths_ready(config)
    device = _torch_device(config.resolved_device())
    _configure_torch_runtime(device)
    model, latest_path, cycle = load_or_create_model(config, device)
    trainer = ReplayTrainer(config, model, device)
    coordinator = SelfPlayCoordinator(config, model.config)
    buffer = PersistentBuffer(config.buffer_dir, config.buffer_size, OBS_DIM, ACTION_SPACE, sparse_limit=config.sparse_limit)
    if not latest_path.exists():
        save_checkpoint(latest_path, model, trainer, cycle, config)
    transitions, stats = coordinator.generate_games(latest_path, config.seed)
    for obs, sparse_policy, mask_indices, targets in transitions:
        buffer.add(obs, sparse_policy, targets, mask_indices)
    buffer.flush()
    print(json.dumps({
        "games": len(stats),
        "buffer_count": buffer.count,
        "avg_turns": float(np.mean([entry.turns for entry in stats])) if stats else 0.0,
        "avg_duration_secs": float(np.mean([entry.duration_secs for entry in stats])) if stats else 0.0,
    }, indent=2))


def run_train_only(config: OvernightConfig) -> None:
    _assert_run_paths_ready(config)
    device = _torch_device(config.resolved_device())
    _configure_torch_runtime(device)
    model, latest_path, cycle = load_or_create_model(config, device)
    trainer = ReplayTrainer(config, model, device)
    buffer = PersistentBuffer(config.buffer_dir, config.buffer_size, OBS_DIM, ACTION_SPACE, sparse_limit=config.sparse_limit)
    if latest_path.exists():
        checkpoint = torch.load(latest_path, map_location=device)
        if "optimizer" in checkpoint:
            trainer.optimizer.load_state_dict(checkpoint["optimizer"])
    if buffer.count < max(config.batch_size, config.min_buffer_samples):
        stats = _zero_train_stats()
    else:
        stats = trainer.train_steps(buffer, config.train_steps_per_cycle)
    save_checkpoint(latest_path, model, trainer, cycle + 1, config)
    print(json.dumps(stats, indent=2))


def parse_args(argv: Optional[Sequence[str]] = None) -> OvernightConfig:
    parser = argparse.ArgumentParser(description="Unified overnight vanilla self-play and training pipeline (CUDA-optimized)")
    parser.add_argument("mode", nargs="?", default="overnight", choices=("overnight", "selfplay", "train", "overfit"))
    parser.add_argument("--run-name", default="vanilla_overnight")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--deck-dir", default=str(DEFAULT_DECK_DIR))
    parser.add_argument("--buffer-dir", default=str(DEFAULT_BUFFER_DIR))
    parser.add_argument("--checkpoint-dir", default=str(DEFAULT_CHECKPOINT_DIR))
    parser.add_argument("--cycles", type=int, default=200)
    parser.add_argument("--max-hours", type=float, default=10.0)
    parser.add_argument("--games-per-cycle", type=int, default=64)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--sims-per-move", type=int, default=128)
    parser.add_argument("--mcts-batch-size", type=int, default=128)
    parser.add_argument("--max-turns", type=int, default=10)
    parser.add_argument("--max-moves", type=int, default=160)
    parser.add_argument("--exploration-turns", type=int, default=4)
    parser.add_argument("--root-dirichlet-alpha", type=float, default=0.30)
    parser.add_argument("--root-dirichlet-eps", type=float, default=0.20)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--teacher-mix", type=float, default=1.0)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--train-steps-per-cycle", type=int, default=48)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--entropy-bonus", type=float, default=3e-4)
    parser.add_argument("--aux-value-weight", type=float, default=0.35)
    parser.add_argument("--buffer-size", type=int, default=120_000)
    parser.add_argument("--sparse-limit", type=int, default=32)
    parser.add_argument("--min-buffer-samples", type=int, default=4096)
    parser.add_argument("--checkpoint-every-cycles", type=int, default=5)
    parser.add_argument("--save-latest-every-cycles", type=int, default=1)
    parser.add_argument("--model-preset", default="small", choices=("tiny", "small", "base", "large", "budget"))
    parser.add_argument("--model-budget-millions", type=float, default=2.5)
    parser.add_argument("--device", default="cuda", choices=("auto", "cpu", "cuda"))
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--fixed-cycle-seed", action="store_true")
    parser.add_argument("--reset-run", action="store_true")
    parser.add_argument("--freeze-selfplay-after-cycle-one", action="store_true")
    parser.add_argument("--mcts-only-selfplay", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--mirror-matches", action="store_true")
    parser.add_argument("--arena-size", type=int, default=0)
    parser.add_argument("--arena-win-threshold", type=float, default=0.55)
    parser.add_argument("--arena-every-cycles", type=int, default=10)
    parser.add_argument("--benchmark-every-cycles", type=int, default=5)
    parser.add_argument("--benchmark-games", type=int, default=16)
    args = parser.parse_args(argv)
    return OvernightConfig(**vars(args))


def main(argv: Optional[Sequence[str]] = None) -> None:
    config = parse_args(argv)
    if config.mode == "selfplay":
        run_selfplay_only(config)
    elif config.mode == "train":
        run_train_only(config)
    elif config.mode == "overfit":
        run_overfit_single_game(config)
    else:
        run_overnight(config)


if __name__ == "__main__":
    main()
