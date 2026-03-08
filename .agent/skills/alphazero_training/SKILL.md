# AlphaZero Training Skill

This skill provides the standard workflow for training AlphaZero models in RabukaSim, specifically focusing on the "Vanilla" (Abilityless) environment.

## 🛠️ Pre-Setup (Mandatory)

Before running any training, ensure the Rust engine and data are in sync. Use the dedicated script in the root:

**PowerShell**:
```powershell
.\rebuild_engine.ps1
```

**CMD / Batch**:
```cmd
rebuild_engine.bat
```

This script builds the engine, links the `.pyd`, compiles the card data, and **starts the training loop** automatically.

## 🚀 Training Workflow

### 1. Continuous Training (Overnight Loop)
For long-term improvement, use the unified script which combines self-play and training into a single iterative cycle.
- **Command**: `uv run python alphazero/training/overnight_vanilla.py`
- **Behavior**: 
    - Spawns parallel workers to generate games.
    - **Ability Stripping**: Automatically strips abilities from cards to ensure a pure vanilla environment.
    - **Buffer**: Trains on a persistent disk-backed experience buffer.
    - **Persistence**: Checkpoints are saved to `vanilla_checkpoints/`.

### 2. Manual Data Generation (Self-Play)
If you want to generate a static dataset for inspection:
- **Command**: `uv run python alphazero/training/generate_vanilla_pure_zero.py --num_games 100 --mirror --verbose`

### 3. Model Training (Static)
If you have a large pre-generated dataset:
- **Command**: `uv run python alphazero/training/vanilla_train.py --data vanilla_trajectories.npz`

## 🧠 Strategic Insights

### Yell & Blade Mechanics
The AI observes yells through two distinct layers:
1. **Input Expectation**: The input tensor contains `ExpectedHearts = AveHeartsPerYell * StageBlades`.
2. **Search Stochasticity (MCTS)**: During MCTS exploration, the engine shuffles the deck and actually rolls the yells for each simulation.

### Positional Invariance
In the vanilla environment, stage slots (Left/Center/Right) are mechanically identical. To accelerate training, actions are mapped to **Card Index Only** (Slot-less mapping).

### Optimized Action Space (Index 0)
The "Select Success Live" action (when multiple cards succeed) is consolidated into **Index 0 (Pass)**. Since the Passing action is disabled by the engine during mandatory selections, there is no ambiguity.

## 🛠️ Verification & Debugging
- **Logs**: Use `--verbose` in `generate` script to see `[Card: Filled/Req OK/FAIL]` status.
- **Throughput**: Monitor `Generation throughput` (Standard: ~0.7-1.0 games/sec).
- **Parity**: Ensure `ACTION_SPACE` (Default: 128) matches across `generate`, `train`, and `model` scripts.
