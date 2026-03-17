# Scenario Training Guide

This guide explains how to use the "Scenario Mode" and "Scenario Mining" features to train the AI on specific mid-game situations (puzzles). This is useful for:
1.  Teaching the AI how to win from complex board states.
2.  Improving performance on end-game logic (Live phase).
3.  Generating massive datasets of real game situations for pre-training.

## 1. Mining Scenarios

To generate a large dataset of game scenarios, use the GPU-accelerated miner. This tool plays thousands of games in parallel using the Numba/CUDA engine and snapshots interesting states.

### Usage

```bash
python ai/mine_scenarios_gpu.py --num 100000 --out data/scenarios_large.npz
```

**Arguments:**
*   `--num`: Number of scenarios to collect (default: 10000).
*   `--out`: Output file path (default: `data/scenarios_large.npz`).

**Performance:**
*   On a consumer GPU (e.g., RTX 3090/4090), this can generate ~100k scenarios in under a minute.
*   The miner uses random/heuristic actions to reach mid-game states (Turn 3-20) where scores are close.

## 2. Training with Scenarios

Once you have a scenario file (e.g., `data/scenarios.npz`), you can configure the training environment to initialize episodes from these states instead of starting new games from scratch.

### Configuration

Set the following environment variables in your training script or shell:

*   `USE_SCENARIOS=1`: Enables scenario loading.
*   `SCENARIO_REWARD_SCALE=0.1`: Scales rewards down (e.g., to 10%) to prevent the AI from overfitting to short-term rewards or messing up its value estimation for full games.

### Example: Running Training

```bash
export USE_SCENARIOS=1
export SCENARIO_REWARD_SCALE=0.1
# Ensure the scenario file exists at data/scenarios.npz or modify the code/symlink
ln -sf data/scenarios_large.npz data/scenarios.npz

# Run the standard optimized training script
python ai/train_vectorized.py
```

### Batch Script

You can create a specialized batch script (e.g., `start_scenario_training.bat` or `.sh`):

```bash
@echo off
set USE_SCENARIOS=1
set SCENARIO_REWARD_SCALE=0.1
python ai/train_vectorized.py
```

## 3. How It Works

1.  **Loading:** When `VectorEnv` (CPU) or `VectorEnvGPU` (GPU) initializes, it loads the `.npz` file into memory.
2.  **Reset:** When an environment resets (either at start or after an episode ends), it randomly selects a scenario from the loaded dataset.
3.  **State Injection:** The environment's internal state buffers (Hand, Deck, Stage, Energy, etc.) are overwritten with the snapshot data.
4.  **Simulation:** The agent plays from that point forward until the game ends or a step limit is reached.
5.  **Reward Scaling:** Rewards returned during these episodes are multiplied by `SCENARIO_REWARD_SCALE`.

## 4. Tips

*   **Dataset Diversity:** Ensure you mine enough scenarios (100k+) to prevent the AI from memorizing specific puzzles.
*   **Curriculum:** You can alternate between Scenario Training and Full Game Training to ensure the AI learns both opening strategies and end-game tactics.
*   **Reward Scale:** Start with `0.1`. If the AI learns too slowly, increase to `0.5`. If it starts playing poorly in full games, decrease it.

## 5. Episode Termination

A common question is: **"When do scenario episodes end?"**

*   **Logic:** Scenarios do **not** automatically end at the end of the turn. They play out until standard game termination conditions are met:
    *   One player reaches 3 Live Points (Win/Loss).
    *   The Deck is empty and cannot be refreshed.
    *   The `GAME_TURN_LIMIT` (default 100) or `GAME_STEP_LIMIT` (default 1000) is reached.
*   **Implication:** This allows the AI to learn multi-turn strategies even if the scenario starts in the middle of a game.

## 6. Puzzle Demo

We have provided a demonstration script to prove the effectiveness of scenario training.

**Script:** `run_puzzle_demo.bat`

**What it does:**
1.  Creates a "Mate-in-1" puzzle (Score 2-2, Agent has winning card).
2.  Runs an untrained agent (Baseline: ~0-5% Win Rate).
3.  Trains a PPO agent on this puzzle for ~20k steps.
4.  Evaluates the trained agent (Result: ~100% Win Rate).

Run this to see the system in action!
