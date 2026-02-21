# Pretraining Techniques Guide

This document describes advanced pretraining techniques implemented to accelerate AI learning for Love Live! SIF Card Game.

## 1. Solitaire Mode (Goldfishing)

**Description:**
In Solitaire Mode, the opponent is present but **never acts** (always passes). This allows the agent to practice its own card combos, resource management, and scoring mechanics without interruption.

**Usage:**
Initialize the environment with `opp_mode=2`.

```python
env = VectorEnv(num_envs=1024, opp_mode=2)
```

**Training Curriculum:**
1.  **Stage 1 (Solitaire):** Train for 1M-10M steps in Solitaire Mode. The agent learns to maximize its own score (reach 3 lives quickly).
2.  **Stage 2 (Heuristic):** Switch to `opp_mode=0` (Heuristic). The agent learns to handle interference.
3.  **Stage 3 (Self-Play):** Switch to `opp_mode=1` (Self-Play/Pool).

## 2. Behavior Cloning (BC)

**Description:**
Behavior Cloning pre-trains the neural network policy to mimic a strong heuristic agent. This initializes the network with a baseline understanding of the game rules and basic strategy (e.g., playing cards on curve, activating abilities) instead of starting from random noise.

**Workflow:**

### Step 1: Generate Dataset
Use the high-speed CPU/Numba engine to simulate games where the agent is controlled by the internal heuristic.

```bash
python ai/generate_bc_data.py --num 100000 --out data/bc_dataset.npz
```
*   Generates 100k samples in seconds.
*   Saves (Observation, Action) pairs.

### Step 2: Train Policy
Train the policy network (Supervised Learning) on the dataset.

```bash
python ai/train_bc.py --data data/bc_dataset.npz --save models/bc_pretrained --epochs 10
```
*   This creates a Stable Baselines 3 compatible model file.

### Step 3: Load & Refine (RL)
Load the pre-trained model and continue training with PPO (Reinforcement Learning).

```python
from sb3_contrib import MaskablePPO

# Load
model = MaskablePPO.load("models/bc_pretrained", env=env)

# Train
model.learn(total_timesteps=10_000_000)
```

**Benefits:**
*   **Faster Convergence:** The agent starts winning immediately against weak opponents.
*   **Exploration:** The heuristic guides the agent to valid/good parts of the state space that random exploration might miss.

## 3. Scenario Training

(See `docs/SCENARIO_TRAINING.md`)
Solving mid-game puzzles to master end-game tactics.
