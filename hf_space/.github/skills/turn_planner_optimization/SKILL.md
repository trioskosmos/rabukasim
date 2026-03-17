---
name: turn_planner_optimization
description: Reference for optimizing the AI turn planner search and heuristics.
---
# Turn Planner Optimization (Vanilla)

## Core Principles
In **Vanilla Mode**, card abilities are disabled. The AI must win through:
1. **Early game (T1-5)**: Build a strong board foundation with blade-heavy members
2. **Mid game (T6-15)**: Establish heart generation engines and identify reachable live cards
3. **Late game (T16+)**: Execute on high-probability wins, preserve energy for key plays

## Strategic Heuristic Architecture

The improved heuristic combines multiple strategic layers:

### Layer 1: Deficit-Driven Heart Placement
- Identify the bottleneck heart color(s) for active lives
- Prioritize cards that fill deficits over redundant hearts
- Heavily penalize placing hearts that don't contribute to current live requirements

### Layer 2: Phased Energy Management
- **Early Game**: Aggressive spending (energy_penalty = 0.05) to build tempo
- **Mid Game**: Moderate spending (energy_penalty = 0.1) balancing board vs reserves
- **Late Game**: Conservative spending (energy_penalty = 0.2+) preserving energy for winning plays
- Consider hand cost distribution: if all remaining cards are expensive, be more conservative

### Layer 3: Live Card Reachability Analysis
- Classify lives in hand as:
  - **Guaranteed**: Board hearts already fulfill requirement (value = 1M + score)
  - **Feasible**: Core hearts + yell can reach requirement (value = score * success_prob)
  - **Fantasy**: Impossible with current resources (value = 0)
- Dynamically adjust live_ev_multiplier based on number of feasible lives:
  - 0 feasible → 20.0 (defensive, focus on board)
  - 1 feasible → 50.0 (moderate push)
  - 2+ feasible → 80.0+ (aggressive race)

### Layer 4: Intelligent Stage Saturation
- Saturation bonus should **discourage** 1-card boards after turn 3
- Progressive bonus: 
  - 1 card at T1-3: 1.0 bonus (acceptable early)
  - 1 card at T4+: -2.0 penalty (too slow)
  - 2 cards: 5.0 bonus (good progress)
  - 3 cards: 12.0+ bonus (synergy multiplier)

### Layer 5: Hand Quality Assessment
- Hand momentum weighted by:
  - Card playability (can hand cost be paid with available energy?)
  - Card utility (heart contribution vs blade contribution)
  - Diversity (having mixed costs is better than all expensive)
- Detect "bricked" hands (all cards unplayable this turn) and heavily penalize

### Layer 6: Move Ordering for Search
- Order candidate moves by heuristic strength:
  - Moves that fill deficits score highest
  - Moves that build toward saturation score medium
  - Moves that are pure tempo (passing) score lowest
- This dramatically improves alpha-beta pruning

## Implementation Details

### Improved `evaluate_members_only_with_weights()`
```
1. Calculate board hearts [0..7]
2. For each active live, calculate color deficits
3. Score each stage card:
   - Base: board_presence weight
   - Blades: multiplied by stage effect weight
   - Hearts:
     a. Deficit hearts: hearts * weights.hearts * 2.0 (HIGH)
     b. Redundant hearts: hearts * weights.hearts * 0.6 (LOW)
     c. Position on stage matters: slot 1 > slot 2 > slot 3 (cascade effect)
4. Apply phased saturation bonus (turn-aware)
5. Apply hand quality momentum assessment (quality-weighted)
6. Apply turn-aware energy penalty (phased)
```

### Improved `predict_best_liveset_score_with_weights()`
```
1. Classify lives as Guaranteed/Feasible/Fantasy
2. Count feasible lives → adjust live_ev_multiplier
3. For each hand life:
   - If Guaranteed: return 1M + score quickly
   - If Feasible: calculate success_prob with uncertainty penalty
   - If Fantasy: return 0
4. Take top-N by EV (N = empty_slots)
```

### Move Ordering Optimization
- Pre-sort actions at shallow depths (depth > 8) using board_state_hash
- Prioritize "deficit-filling" moves in sort order
- Use quick heuristic approximation for deep searches

## Performance Baseline
- Game Time (20 turns): ~3.5s
- Per-turn Average: ~0.17s
- Late-game Evals: ~900-1500

## Current Weights
- `board_presence`: 2.5 (base stage presence value)
- `blades`: 3.5 (yell multiplier)
- `hearts`: 1.5 (heart multiplier - adjusted per deficit)
- `saturation_bonus`: 8.0 (turn-aware bonus, ranges 0.5-12.0)
- `energy_penalty`: 0.1 (phased, 0.05-0.2 range)
- `live_ev_multiplier`: 55.0 (dynamic, 20-80 range)
- `uncertainty_penalty_pow`: 1.1 (success probability exponent)
- `liveset_placement_bonus`: 12.0 (cycling bonus)
- `cycling_bonus`: 4.5 (draw potential per placed card)
