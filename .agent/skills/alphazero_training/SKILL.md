---
name: alphazero_training
description: Principles and implementation for AlphaZero/MCTS training and optimization.
---

# AlphaZero Training Skill

This skill governs the architectural patterns, mathematical heuristics, and training workflows required for implementing AlphaZero-style AI in LovecaSim.

## Core Principles

1. **Performance over Precision**: Use linear heuristics (Expected Value) inside MCTS loops rather than exact combinatorial math (Hypergeometric) to maximize tree search throughput.
2. **State Representation**: Game state must be flattened into fixed-size tensors for neural network consumption while preserving spatial/relational context (e.g., stage slot order).
3. **Hybrid Solvers**: Use analytical solvers (like `PerformanceProbabilitySolver`) to bootstrap value networks or provide "checks" on the policy network's legality.

## Workflow

1. **Analytical Baseline**: Verify engine logic using `test_performance_solver.rs`.
2. **Heuristic Profiling**: Measure the throughput of the analysis layer to ensure it doesn't bottleneck MCTS.
3. **Data Collection**: Export game traces where the analytical solver provides "ground truth" labels for success probability.

## Resources
- [MCTS Performance Principles](resources/mcts_performance_principles.md)
- `engine_rust_src/src/core/analysis/performance_solver.rs` (Implementation Reference)
