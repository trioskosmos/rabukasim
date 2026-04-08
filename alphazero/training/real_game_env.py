from __future__ import annotations

import importlib.util
import json
import random
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

try:
    from gymnasium import Env, spaces
except ImportError:  # pragma: no cover - optional in lightweight environments
    Env = object  # type: ignore[misc,assignment]

    class _Box:
        def __init__(self, low, high, shape, dtype):
            self.low = low
            self.high = high
            self.shape = shape
            self.dtype = dtype

    class _Discrete:
        def __init__(self, n: int):
            self.n = int(n)

    spaces = SimpleNamespace(Box=_Box, Discrete=_Discrete)  # type: ignore[assignment]

from alphazero.training.action_codec import (
    ACTION_SPACE,
    build_legal_policy_context,
    engine_action_to_policy_id,
    policy_id_to_engine_action,
)
from alphazero.training.action_features import (
    build_candidate_action_features,
    resolve_card_context_for_action,
)
from alphazero.training.vanilla_observation import build_card_feature_lookup


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = ROOT_DIR / "data" / "cards_compiled.json"
DEFAULT_DB_FALLBACKS = (
    DEFAULT_DB_PATH,
    ROOT_DIR / "data" / "archive" / "20260329_032051" / "cards_compiled.json",
    ROOT_DIR / "engine" / "data" / "cards_compiled.json",
    ROOT_DIR / "launcher" / "static_content" / "data" / "cards_compiled.json",
)
DEFAULT_ENGINE_PYD = ROOT_DIR / "engine_rust_src" / "target" / "release" / "engine_rust_training.pyd"
DEFAULT_ENGINE_DLL = ROOT_DIR / "engine_rust_src" / "target" / "release" / "engine_rust.dll"

OBSERVATION_DIM = 1200

_ENGINE_MODULE: Any | None = None


def _resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT_DIR / path


def load_compiled_database_json(db_path: str | Path = DEFAULT_DB_PATH) -> tuple[dict[str, Any], str]:
    candidates = [_resolve_path(db_path)]
    for fallback in DEFAULT_DB_FALLBACKS:
        resolved = _resolve_path(fallback)
        if resolved not in candidates:
            candidates.append(resolved)

    last_error: Exception | None = None
    for resolved in candidates:
        if not resolved.exists():
            continue
        try:
            full_db = json.loads(resolved.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - invalid file fallback
            last_error = exc
            continue
        if any(full_db.get(section) for section in ("member_db", "live_db", "energy_db")):
            return full_db, json.dumps(full_db)

    if last_error is not None:
        raise last_error
    raise FileNotFoundError("No populated cards_compiled.json was found")


def _ensure_engine_importable() -> None:
    if DEFAULT_ENGINE_DLL.exists():
        needs_refresh = not DEFAULT_ENGINE_PYD.exists()
        if not needs_refresh:
            needs_refresh = DEFAULT_ENGINE_DLL.stat().st_mtime > DEFAULT_ENGINE_PYD.stat().st_mtime
        if needs_refresh:
            DEFAULT_ENGINE_PYD.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(DEFAULT_ENGINE_DLL, DEFAULT_ENGINE_PYD)


def _load_engine_module():
    global _ENGINE_MODULE
    if _ENGINE_MODULE is not None:
        return _ENGINE_MODULE

    _ensure_engine_importable()
    sys.modules.pop("engine_rust", None)
    spec = importlib.util.spec_from_file_location("engine_rust", DEFAULT_ENGINE_PYD)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load engine module from {DEFAULT_ENGINE_PYD}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["engine_rust"] = module
    spec.loader.exec_module(module)
    _ENGINE_MODULE = module
    return _ENGINE_MODULE


def _build_deck_pool(full_db: dict[str, Any]) -> tuple[list[int], list[int], list[int]]:
    member_ids = [int(cid) for cid in full_db.get("member_db", {}).keys()]
    live_ids = [int(cid) for cid in full_db.get("live_db", {}).keys()]
    energy_ids = [int(cid) for cid in full_db.get("energy_db", {}).keys()]
    if not member_ids or not live_ids or not energy_ids:
        raise ValueError("Compiled card database is missing member, live, or energy cards")
    return member_ids, live_ids, energy_ids


def _sample_deck(rng: random.Random, member_ids: list[int], live_ids: list[int], energy_ids: list[int]) -> tuple[list[int], list[int], list[int]]:
    members = list(member_ids)
    lives = list(live_ids)
    energy = list(energy_ids)
    rng.shuffle(members)
    rng.shuffle(lives)
    rng.shuffle(energy)
    main_deck = (members[:48] + lives[:12])[:60]
    if len(main_deck) < 60:
        raise ValueError(f"Expected a 60-card main deck, got {len(main_deck)}")
    return main_deck, energy[:12], lives[:12]


def _count_legal_policy_ids(legal_mask: np.ndarray) -> np.ndarray:
    mask = np.asarray(legal_mask, dtype=np.bool_)
    return np.flatnonzero(mask)


@dataclass(slots=True)
class RealGameEnvConfig:
    db_path: str | Path = DEFAULT_DB_PATH
    seed: int | None = None
    matchup_mode: str = "mixed"
    max_turns: int = 10
    reward_on_timeout: float = -1.0


class RealGameEnv(Env):
    """Headless RL env backed by the Rust engine source tree."""

    metadata = {"render_modes": ["json", "human"]}

    def __init__(self, config: RealGameEnvConfig | None = None):
        self.config = config or RealGameEnvConfig()
        self.full_db, self.db_json = load_compiled_database_json(self.config.db_path)
        self._engine = _load_engine_module()
        self.db = self._engine.PyCardDatabase(self.db_json)
        self.card_lookup = build_card_feature_lookup(self.full_db)
        self.member_ids, self.live_ids, self.energy_ids = _build_deck_pool(self.full_db)

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(int(OBSERVATION_DIM),),
            dtype=np.float32,
        )
        self.action_space = spaces.Discrete(int(ACTION_SPACE))

        self.state = None
        self._rng = random.Random(self.config.seed)
        self._episode_index = 0
        self._deck_pair: tuple[dict[str, Any], dict[str, Any]] | None = None
        self._last_info: dict[str, Any] = {}

    def _seed_world(self, seed: int | None) -> None:
        if seed is None:
            return
        self._rng = random.Random(int(seed))
        random.seed(int(seed))
        np.random.seed(int(seed) % (2**32 - 1))

    def _make_game(self):
        state = self._engine.PyGameState(self.db)
        state.silent = True
        state.debug_mode = False
        return state

    def _current_initial_deck(self) -> list[int]:
        if self.state is None or self._deck_pair is None:
            return []
        current_player = int(self.state.current_player)
        if current_player == 0:
            return list(self._deck_pair[0]["initial_deck"])
        return list(self._deck_pair[1]["initial_deck"])

    def _state_tensor(self) -> np.ndarray:
        if self.state is None:
            raise RuntimeError("Environment has not been reset")
        obs = np.asarray(self.state.to_vanilla_tensor(), dtype=np.float32)
        if obs.shape[0] != OBSERVATION_DIM:
            raise RuntimeError(f"Expected Rust observation length {OBSERVATION_DIM}, got {obs.shape[0]}")
        return obs

    def _state_json(self) -> dict[str, Any]:
        if self.state is None:
            raise RuntimeError("Environment has not been reset")
        return json.loads(self.state.to_json())

    def _legal_context(self) -> tuple[np.ndarray, np.ndarray, dict[int, int]]:
        if self.state is None:
            return np.zeros(int(ACTION_SPACE), dtype=np.bool_), np.zeros(0, dtype=np.int64), {}
        legal_engine_actions = [int(action_id) for action_id in self.state.get_legal_action_ids()]
        return build_legal_policy_context(legal_engine_actions, self._current_initial_deck(), int(self.state.phase))

    def _describe_engine_action(self, state_json: dict[str, Any], engine_action: int) -> dict[str, Any]:
        if self.state is None:
            return {"engine_action": int(engine_action)}

        label = self.state.get_verbose_label(int(engine_action))
        mapped_policy_id = int(
            engine_action_to_policy_id({}, int(engine_action), self._current_initial_deck(), int(self.state.phase))
        )
        return resolve_card_context_for_action(
            state_json,
            int(self.state.current_player),
            label,
            int(engine_action),
            mapped_policy_id,
            0 <= mapped_policy_id < int(ACTION_SPACE),
            int(self.state.turn),
            int(self.state.phase),
        )

    def _legal_action_details(self, state_json: dict[str, Any]) -> list[dict[str, Any]]:
        if self.state is None:
            return []
        legal_actions = []
        for engine_action in [int(x) for x in self.state.get_legal_action_ids()]:
            record = self._describe_engine_action(state_json, engine_action)
            legal_actions.append(record)
        return legal_actions

    def _build_info(self) -> dict[str, Any]:
        if self.state is None:
            return {}
        state_json = self._state_json()
        legal_mask, legal_policy_ids, mapping = self._legal_context()
        legal_actions = self._legal_action_details(state_json)
        candidate_features = build_candidate_action_features(legal_actions, self.card_lookup)
        return {
            "episode_index": int(self._episode_index),
            "turn": int(self.state.turn),
            "phase": int(self.state.phase),
            "current_player": int(self.state.current_player),
            "winner": int(self.state.get_winner()) if bool(self.state.is_terminal()) else -1,
            "legal_action_ids": [int(x) for x in self.state.get_legal_action_ids()],
            "legal_policy_ids": [int(x) for x in legal_policy_ids.tolist()],
            "legal_actions": legal_actions,
            "candidate_actions": legal_actions,
            "candidate_action_features": candidate_features,
            "candidate_action_ids": np.asarray([int(action["engine_action"]) for action in legal_actions], dtype=np.int64),
            "candidate_action_policy_ids": np.asarray([int(action.get("mapped_policy_id", -1)) for action in legal_actions], dtype=np.int64),
            "raw_legal_action_ids": [int(x) for x in self.state.get_legal_action_ids()],
            "action_mask": legal_mask,
            "legal_action_mask": legal_mask,
            "engine_action_map": mapping,
            "state_json": self.state.to_json(),
            "state_dict": state_json,
        }

    def _advance_auto_actions(self) -> None:
        if self.state is None:
            return
        safety = 0
        while not self.state.is_terminal() and safety < 128:
            legal_ids = [int(action_id) for action_id in self.state.get_legal_action_ids()]
            if len(legal_ids) != 1 or int(legal_ids[0]) != 0:
                break
            self.state.step(0)
            self.state.auto_step(self.db)
            safety += 1

    def _apply_timeout_rule(self, acting_player: int) -> tuple[float, bool, bool, dict[str, Any]]:
        if self.state is None:
            return 0.0, False, False, {}
        if bool(self.state.is_terminal()):
            winner = int(self.state.get_winner())
            reward = 0.0 if winner == -1 else (1.0 if winner == acting_player else -1.0)
            return reward, True, False, {}

        if self.config.max_turns > 0 and int(self.state.turn) >= self.config.max_turns:
            return float(self.config.reward_on_timeout), False, True, {"turn_limit_reached": True}

        return 0.0, False, False, {}

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
        if hasattr(super(), "reset"):
            super().reset(seed=seed)
        if seed is not None:
            self._seed_world(seed)
        elif self.config.seed is not None and self.state is None:
            self._seed_world(self.config.seed)

        self._episode_index = int(options.get("episode_index", 0)) if options else 0

        main_left, energy_left, lives_left = _sample_deck(self._rng, self.member_ids, self.live_ids, self.energy_ids)
        if self.config.matchup_mode == "mirror":
            main_right, energy_right, lives_right = list(main_left), list(energy_left), list(lives_left)
        else:
            main_right, energy_right, lives_right = _sample_deck(self._rng, self.member_ids, self.live_ids, self.energy_ids)

        self._deck_pair = (
            {
                "initial_deck": list(main_left),
                "energy": list(energy_left),
                "lives": list(lives_left),
            },
            {
                "initial_deck": list(main_right),
                "energy": list(energy_right),
                "lives": list(lives_right),
            },
        )

        self.state = self._make_game()
        self.state.initialize_game_with_seed(
            list(main_left),
            list(main_right),
            list(energy_left),
            list(energy_right),
            list(lives_left),
            list(lives_right),
            int(self._rng.getrandbits(63)),
        )
        self._advance_auto_actions()

        obs = self._state_tensor()
        info = self._build_info()
        self._last_info = info
        return obs, info

    def step(self, action: int):
        if self.state is None:
            raise RuntimeError("Environment must be reset before stepping")

        if bool(self.state.is_terminal()):
            obs = self._state_tensor()
            info = self._build_info()
            return obs, 0.0, True, False, info

        acting_player = int(self.state.current_player)
        phase = int(self.state.phase)
        policy_id = int(action)
        legal_mask, legal_policy_ids, mapping = self._legal_context()
        raw_legal_actions = {int(x) for x in self.state.get_legal_action_ids()}

        engine_action: int | None = None
        input_mode = "policy"
        if 0 <= policy_id < int(ACTION_SPACE) and bool(legal_mask[policy_id]):
            engine_action = policy_id_to_engine_action(
                self.state,
                acting_player,
                policy_id,
                phase,
                self._current_initial_deck(),
            )
            if engine_action is None:
                raise ValueError(f"No engine action mapping for policy action {policy_id}")
        elif policy_id in raw_legal_actions:
            engine_action = policy_id
            input_mode = "engine"
        else:
            raise ValueError(f"Illegal action {policy_id} in phase {phase}")

        self.state.step(int(engine_action))
        self.state.auto_step(self.db)
        self._advance_auto_actions()

        reward, terminated, truncated, timeout_info = self._apply_timeout_rule(acting_player)
        obs = self._state_tensor()
        info = self._build_info()
        current_legal_mask, current_legal_policy_ids, current_mapping = self._legal_context()
        info.update(timeout_info)
        info["action"] = policy_id
        info["engine_action"] = int(engine_action)
        info["input_mode"] = input_mode
        info["legal_policy_ids"] = [int(x) for x in current_legal_policy_ids.tolist()]
        info["action_mask"] = current_legal_mask
        info["legal_action_mask"] = current_legal_mask
        info["engine_action_map"] = current_mapping
        self._last_info = info
        return obs, float(reward), bool(terminated), bool(truncated), info

    def action_masks(self) -> np.ndarray:
        mask, _, _ = self._legal_context()
        return mask

    def render(self):
        if self.state is None:
            return None
        return self.state.to_json()

    def close(self):
        self.state = None
        self._deck_pair = None


def make_real_game_env(config: RealGameEnvConfig | None = None, **overrides: Any) -> RealGameEnv:
    base = config or RealGameEnvConfig()
    data = asdict(base)
    data.update(overrides)
    return RealGameEnv(RealGameEnvConfig(**data))


__all__ = [
    "RealGameEnvConfig",
    "RealGameEnv",
    "make_real_game_env",
    "load_compiled_database_json",
]
