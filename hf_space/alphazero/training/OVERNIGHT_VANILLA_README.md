# Overnight Vanilla Self-Play Trainer

## Overview
`alphazero/training/overnight_vanilla.py` is the canonical abilityless training loop.

It now uses the engine's native vanilla encoding and action mapping instead of a hand-rolled placeholder observation path.

## Key Features

### Self-Play (No Cheating)
- **Public-information input only**: observations come from `state.to_vanilla_tensor()`.
- **Single-deck mirror self-play**: both sides use the same configured deck.
- **Search-improved policy targets**: engine MCTS suggestions are stored as soft targets.
- **Scalar value head**: predicts position strength in `[-1, 1]`.
- **Deterministic setup skip**: RPS and turn-order setup are resolved automatically so training focuses on gameplay decisions.

### GPU Optimization
- **Mixed precision (AMP)**: FP16/FP32 automatic casting
- **Persistent replay buffer**: disk-backed replay via `PersistentBuffer`
- **Batch training**: Efficient gradient accumulation
- **Gradient clipping**: Stable optimization

### Architecture
- **Model**: `HighFidelityAlphaNet` (transformer-based)
  - Configurable preset: tiny/small/base/large
  - Engine-native vanilla layout: 20 global features + 60 cards x 13 features
  - Zone, type, position, and phase embeddings
  
- **Observation**: dense 800D vanilla tensor
  - 20 global features
  - 60 card slots x 13 features
  - Configurable observation modes:
    - `raw`: strips portfolio and success-probability hints
    - `human_hint`: keeps summary odds, removes participation-bit oracle hints
    - `full`: keeps the full engine vanilla tensor
  
- **Actions**: compact 109-action policy space
  - RPS and turn-order setup
  - mulligans
  - live selection
  - main-phase hand-to-stage plays
  - live result selection

## Configuration

Edit `OvernightConfig` or `SelfPlayConfig` in the trainer:
```python
config = SelfPlayConfig(
    deck_source="ai/decks/muse_cup.txt",
    db_path="data/cards_vanilla.json",
    model_preset="small",
    observation_mode="human_hint",
    games_per_iteration=24,
    training_steps_per_iteration=96,
    batch_size=128,
    search_sims=32,
    device="cuda",
)
```

## Running

```bash
# Training
python alphazero/training/overnight_vanilla.py

# Via entrypoint
python ai/training/vanilla_loop.py

# Fast runtime check
python alphazero/training/overnight_vanilla.py smoke --model-preset tiny --search-sims 1 --max-turns 1

# Fast proof probe
python alphazero/training/overnight_vanilla.py proof --model-preset tiny --search-sims 4 --max-turns 3

# Fixed-seed benchmark vs greedy and search
python alphazero/training/overnight_vanilla.py benchmark --device cuda --benchmark-games 24 --search-sims 12

# Include a small turn-sequencer benchmark lane in periodic evals
python alphazero/training/overnight_vanilla.py train --turnseq-benchmark-games 4

# Root launcher for tuned overnight training
run_vanilla_overnight.bat
```

## Output Structure
```
checkpoints/vanilla_overnight/   # Model checkpoints
  latest.pt
  iter_00000.pt
  iter_00001.pt
  ...

buffers/vanilla_overnight/       # Replay buffer (mmap'd)
  obs.npy                        # Observations
  p_idx.npy, p_val.npy           # Sparse policies
  values.npy                     # Win/loss targets
  masks.npy                      # Legal action masks
  meta.json                      # Buffer metadata

checkpoints/vanilla_overnight/
  benchmark_log.csv              # Fixed-seed benchmark results vs greedy/search
```

## Dependency: engine_rust
The trainer **requires `engine_rust` compiled module** to play games. This is the C++/Rust game engine that:
- Simulates game states
- Returns legal actions
- Evaluates terminal states
- Provides JSON serialization

If `engine_rust` is unavailable, games cannot be simulated (graceful degradation with error logs).

## Design Principles

1. **No Cheating**: Only public game information in observations
2. **Self-Play Loop**: The acting policy is the current model; search supplies improved targets.
  Early training is intentionally teacher-guided so a weak model does not generate low-quality random games.
3. **Human-Hint Mode**: Expected clear odds and deck-counting summaries can be exposed without full participation-bit oracle hints.
4. **Interrupt Safety**: `Ctrl+C` now stops at the next safe point, flushes the replay buffer, and writes an atomic `latest.pt` checkpoint before exiting.
5. **Live Monitoring**: Per-iteration terminal logs now include game count, average turns, decisive/draw totals, pass rate, teacher-forced rate, and teacher-match rates in addition to loss terms.
4. **Persistent State**: Checkpoints and replay buffer survive process restarts
5. **GPU-First**: Full training is intended for CUDA. CPU is useful for smoke checks and tiny proof probes only.
6. **Single Responsibility**: Trainer orchestrates, engine computes legal state/search, model learns compact policy/value heads.

## Next Steps
- [ ] Monitor training loss/convergence
- [ ] Benchmark against random and greedy baselines over full games on GPU
- [ ] Tune model size (tiny/small/large) for hardware
- [ ] Decide whether `human_hint` or `full` is the long-term default
- [ ] Add a full-game proof harness that runs on GPU budgets rather than CPU-only probe datasets
