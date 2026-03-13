---
name: turn_planner_optimization
description: Reference for optimizing the AI turn planner search and heuristics.
---
# Turn Planner Optimization (Vanilla)

## Core Principles
In **Vanilla Mode**, card abilities are disabled. The AI must win through optimal placement of Member cards for heart generation and efficient Live card success.

## Performance Baseline
- Game Time (20 turns): ~3.5s
- Per-turn Average: ~0.17s
- Late-game Evals: ~900-1500

## Vanilla Heuristics
The AI evaluates positions based on `WeightsConfig`:
- `board_presence`: Stage presence is the primary objective.
- `blades`: Yells are critical (stage blades + bonuses).
- `hearts`: Direct heart generation.
- `saturation_bonus`: Critical bonus for filling all 3 stage slots.
- `energy_penalty`: Efficiency of energy usage.
- `live_ev_multiplier`: Expected value of live card completion.

## Absolute Priority (Guaranteed Clears)
To ensure the AI prioritizes winning over efficiency:
1. **Guaranteed Success Bonus**: If a Live card has a 100% (or overflow 120%) probability of success based on current board state, it receives an **Absolute Priority** score: `1,000,000.0 + live.score`.
2. **Implementation**:
    - `live_card_expected_value_with_weights`: Returns `1,000,000.0 + score` if `prob >= 1.2`.
    - `live_card_heuristic_approximation`: Returns `1,000,000.0 + score` if context confirms board hearts already satisfy requirements.
3. **Rationale**: This forces the turn sequencer to pick any branch that results in a guaranteed clear, regardless of energy cost or synergy.

## Speed-to-Win Configuration
For maximum aggression, the weights are tuned as:
- **Energy Penalty**: Reduced (e.g., `0.05`) to encourage high-cost, high-impact plays.
- **Board Presence**: Increased (e.g., `7.0`) to maximize heart output per turn.
- **Blades**: Increased (e.g., `5.0`) to reveal Yells faster.

## Priority One Audit (Logging)
- Use `simple_game --verbose-search` or un-silence `println!` blocks in `execute_main_sequence` to audit AI branches.
- `heuristic_log.csv` captures the breakdown of these high-priority scores for offline analysis.

## Optimization Techniques
1. **Heuristic Approximation**: Use O(1) checks for live card success potential instead of full probability calculations in search nodes.
2. **Simplified Context**: Avoid expensive hand iteration when estimating future yell potential; use stage blades directly.
3. **Weight Tuning**: Fine-tuning the balance between filling the board and saving energy for high-value plays.

### Search Config
- `max_dfs_depth`: 15 (Standard) / 24 (Vanilla Exhaustive).
- `vanilla_exact_turn_threshold`: 200,000 sequences.
