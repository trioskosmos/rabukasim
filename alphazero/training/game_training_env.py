from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from alphazero.training.real_game_env import (
    RealGameEnv,
    RealGameEnvConfig,
    load_compiled_database_json,
)


@dataclass(slots=True)
class GameTrainingEnvConfig(RealGameEnvConfig):
    """Minimal training env config.

    This keeps the same engine-backed behavior as `RealGameEnv`, but the
    exposed `info` payload is intentionally small so an agent can focus on
    learning the game rather than consuming trainer-specific metadata.
    """


class GameTrainingEnv(RealGameEnv):
    """A minimal headless environment for learning the game.

    The engine behavior is the same as `RealGameEnv`:
    - live Rust engine
    - automatic resolution
    - abilities and prompts enabled
    - turn-10 timeout

    The difference is that the returned `info` only includes the essentials:
    current turn, phase, player, winner, legal action ids, and the action mask.
    """

    def _build_info(self) -> dict[str, Any]:
        if self.state is None:
            return {}
        legal_mask, legal_policy_ids, _ = self._legal_context()
        return {
            "episode_index": int(self._episode_index),
            "turn": int(self.state.turn),
            "phase": int(self.state.phase),
            "current_player": int(self.state.current_player),
            "winner": int(self.state.get_winner()) if bool(self.state.is_terminal()) else -1,
            "turn_limit_reached": False,
            "legal_action_ids": [int(x) for x in self.state.get_legal_action_ids()],
            "legal_policy_ids": [int(x) for x in legal_policy_ids.tolist()],
            "action_mask": legal_mask,
            "legal_action_mask": legal_mask,
        }

    def step(self, action: int):
        obs, reward, terminated, truncated, info = super().step(action)
        # Keep the minimal env's info compact even after step().
        info = {
            "episode_index": info.get("episode_index", int(self._episode_index)),
            "turn": info.get("turn", int(self.state.turn) if self.state is not None else -1),
            "phase": info.get("phase", int(self.state.phase) if self.state is not None else -1),
            "current_player": info.get("current_player", int(self.state.current_player) if self.state is not None else -1),
            "winner": info.get("winner", -1),
            "turn_limit_reached": bool(info.get("turn_limit_reached", False)),
            "legal_action_ids": info.get("legal_action_ids", []),
            "legal_policy_ids": info.get("legal_policy_ids", []),
            "action_mask": info.get("action_mask", np.zeros(0, dtype=np.bool_)),
            "legal_action_mask": info.get("legal_action_mask", np.zeros(0, dtype=np.bool_)),
        }
        return obs, reward, terminated, truncated, info


def make_game_training_env(config: GameTrainingEnvConfig | None = None, **overrides: Any) -> GameTrainingEnv:
    base = config or GameTrainingEnvConfig()
    data = asdict(base)
    data.update(overrides)
    return GameTrainingEnv(GameTrainingEnvConfig(**data))


__all__ = [
    "GameTrainingEnvConfig",
    "GameTrainingEnv",
    "make_game_training_env",
    "load_compiled_database_json",
]
