# Real Game Environment

`alphazero/training/real_game_env.py` is the trainer-facing Rust engine wrapper.

If you want the simplest environment for an agent to learn the game, use:

- [`alphazero/training/game_training_env.py`](./GAME_TRAINING_ENVIRONMENT.md)

## When to use this file

Use `RealGameEnv` only when you need the richer action metadata for:

- trainer-side candidate scoring
- debugging action mappings
- inspecting engine action labels and card context

## When not to use this file

Do not use `RealGameEnv` as the default learning surface unless you need the extra metadata.
For a plain learning loop, `GameTrainingEnv` is the smaller and cleaner API.

