# AI Configuration Guide

This document references all environment variables used to configure the AI training pipeline, game engine settings, and pretraining modes.

## Training Configuration (`ai/train_vectorized.py`)

These variables control the PPO training hyperparameters and resource usage.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `USE_GPU_ENV` | `0` | Set to `1` to enable the GPU-resident environment (`VectorEnvGPU`). Requires CUDA. |
| `TRAIN_ENVS` | `4096` | Number of parallel environments to run. (e.g. `256` for CPU, `4096`+ for GPU). |
| `TRAIN_BATCH_SIZE` | `8192` | Size of the batch used for PPO updates. Should be a multiple of `TRAIN_ENVS`. |
| `TRAIN_N_STEPS` | `256` | Number of steps to run per environment per rollout. |
| `TRAIN_STEPS` | `100_000_000` | Total number of timesteps to train for. |
| `LEARNING_RATE` | `3e-4` | Learning rate for the PPO optimizer. |
| `NUM_EPOCHS` | `4` | Number of epochs to optimize the surrogate loss per PPO update. |
| `ENT_COEF` | `0.01` | Entropy coefficient for exploration. |
| `GAMMA` | `0.99` | Discount factor. |
| `GAE_LAMBDA` | `0.95` | GAE parameter. |
| `OBS_MODE` | `STANDARD` | Observation space mode. Options: `STANDARD` (2304-dim), `IMAX` (8192-dim), `ATTENTION` (2240-dim), `COMPRESSED` (512-dim). |
| `LOAD_CHECKPOINT` | `""` | Path to a `.zip` model file to resume training from. |
| `SAVE_FREQ_MINS` | `15.0` | Frequency (in minutes) to save checkpoints. |

## Game Engine Configuration (`ai/vector_env.py`)

These variables tweak the rules and rewards of the environment itself.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `GAME_TURN_LIMIT` | `100` | Maximum number of turns before a game is forcibly ended (draw/loss). |
| `GAME_STEP_LIMIT` | `1000` | Maximum number of individual actions/steps before truncation. |
| `GAME_REWARD_WIN` | `100.0` | Reward bonus for winning a game. |
| `GAME_REWARD_LOSE` | `-100.0` | Reward penalty for losing a game. |
| `GAME_REWARD_SCORE_SCALE` | `50.0` | Multiplier for the score difference (My Score - Opp Score). |
| `GAME_REWARD_TURN_PENALTY` | `-0.05` | Penalty applied every step to encourage faster wins. |
| `USE_FIXED_DECK` | (None) | Path to a deck file (`.md` or `.json`) to force both players to use a specific deck. |

## Scenario Mode (`docs/SCENARIO_TRAINING.md`)

Configuration for training on pre-generated puzzle states.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `USE_SCENARIOS` | `0` | Set to `1` to enable loading states from `data/scenarios.npz`. |
| `SCENARIO_REWARD_SCALE` | `1.0` | Factor to scale rewards during scenario training (e.g. `0.1` to reduce variance). |

## Pretraining Modes (`docs/PRETRAINING.md`)

These are typically set via arguments or code, but influence the environment behavior.

*   **Solitaire Mode**: Initialize `VectorEnv(opp_mode=2)`. The opponent passes every turn.
*   **Heuristic Opponent**: Initialize `VectorEnv(opp_mode=0)`. Default hard-coded logic.
*   **Random Opponent**: Initialize `VectorEnv(opp_mode=1)`. Random legal moves.

## Example: Speed Demon Training

To run a high-throughput GPU training session:

```bash
export USE_GPU_ENV=1
export TRAIN_ENVS=8192
export TRAIN_BATCH_SIZE=32768
export OBS_MODE=COMPRESSED
python ai/train_vectorized.py
```
