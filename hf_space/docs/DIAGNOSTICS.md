# Lovecasim AI Diagnostics Guide

This document explains how to analyze AI decision-making, adjust strategic weights, and troubleshoot engine behavior.

## 🏛️ AI Architecture (Decoupled)

The AI is split into two layers to separate search logic from game-specific strategy:
- **Search Engine (`mcts.rs`)**: Implements Monte Carlo Tree Search. It is strategy-agnostic and uses the `Heuristic` trait.
- **Strategy Layer (`heuristics.rs`)**: Contains all scoring logic, evaluation weights, and the `OriginalHeuristic` implementation. **This is where you make balance changes.**

---

## 1. Diagnostic Workflows

To analyze why the AI made a specific move, use the following steps.

### Step 1: Rebuild & Sync
Whenever you modify `heuristics.rs` or `mcts.rs`:
```powershell
cd engine_rust_src
cargo build --release
copy target\release\engine_rust.dll ..\engine_rust.pyd
cd ..
```

### Step 2: Run Verbose Simulation
The tournament script can run a single game with full scoring breakdowns:
```powershell
uv run python tools/heuristics_tournament.py --debug
```
- **`debug_game.log`**: Generated in the root. Contains per-move hand state and the top 10 scored actions.
- **Top 10 Actions**: Shows the normalized score [0-1] for each legal move after MCTS simulations.

---

## 2. Tuning Strategy (`heuristics.rs`)

All core weights live in `engine_rust_src/src/core/heuristics.rs` inside `evaluate_player`.

### Key Strategic Weights
| Category | Weight | Logic / Purpose |
| :--- | :--- | :--- |
| **Slot Penalty** | `-1000.0` | Forces AI to prioritize filling all 3 stage slots immediately. |
| **Board Power** | `100.0` | Multiplied by member cost. Encourages playing higher-tier cards. |
| **Hearts** | `50.0` | Rewards guaranteed Stage Hearts. |
| **Live Value** | `100.0` | Multiplied by `live.score`. Prioritizes 2-point lives over 1-point lives. |
| **Success Bonus** | `100.0` | Flat bonus if `success_lives.len() > baseline`. Drives win progression. |

### Diagnostic Breakdown
The engine prints a breakdown of the score for the current player in the terminal/log:
`Lives: 200.0, Power: 900.0, Hearts: 150.0, Slots: 3/3 (+300.0), Total: 1550.0`

---

## 3. Heuristic Scaling

We convert raw board scores into a normalized "Utility" for the MCTS engine.

- **Scaling Factor**: `0.0001`
- **Formula**: `(Score_Gap * 0.0001) + 0.5`
- **Utility Range**: Clips to `[0.0, 1.0]`.
  - `1.0` = Absolute crushing victory.
  - `0.5` = Perfectly even board.
  - `0.0` = Total loss.

> [!TIP]
> If all actions in `debug_game.log` show `1.0000`, the scaling is too aggressive (gap is too wide). Reduce the factor to `0.00005`.

---

## 4. Common Troubleshooting

### AI "Passes" constantly (Selected Action 0)
1. **Low Slot Penalty**: If action 0 (Passing) is selected over playing a card, increase the `-1000.0` penalty for empty slots.
2. **Missing Hearts**: If the AI won't play lives, verify `proximity_score` in `heuristics.rs` is correctly calculating heart sufficiency.

### AI ignores high-point lives
Check the `Live Value` multiplier. If most lives have `score: 1`, the AI might see them as equal. Increasing the weight (e.g., to `500.0`) forces a stronger preference for 2-point lives.

### Simulation is too slow
Adjust `sims` in `heuristics_tournament.py` (Default: 5000). For quick tuning, `500` - `1000` is usually sufficient to see the heuristic's intent.
