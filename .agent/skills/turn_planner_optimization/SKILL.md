---
name: turn_planner_optimization
description: Use when adjusting search heuristics, move ordering, pruning, or turn-planner performance.
---
# Turn Planner Optimization
## Do
- Change one heuristic at a time.
- Measure before and after.
- Keep scoring, pruning, and branching effects separate.
## Do not
- Do not tune blindly without a baseline.
- Do not mix unrelated performance changes.
## Verify
- Run the benchmark or regression set and compare results.