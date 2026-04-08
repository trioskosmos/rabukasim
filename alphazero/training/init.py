from __future__ import annotations

from alphazero.training.game_training_env import (
    GameTrainingEnv,
    GameTrainingEnvConfig,
    load_compiled_database_json,
    make_game_training_env,
)

__all__ = [
    "GameTrainingEnvConfig",
    "GameTrainingEnv",
    "make_game_training_env",
    "load_compiled_database_json",
]


if __name__ == "__main__":
    env = make_game_training_env()
    obs, info = env.reset()
    print(obs.shape, info.get("current_player"))
