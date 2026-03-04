---
name: alphazero_training
description: Principles and implementation for AlphaZero/MCTS training and optimization.
---

# AlphaZero Training Skill

This skill governs the architectural patterns, mathematical heuristics, and training workflows required for implementing AlphaZero-style AI in LovecaSim.

## Core Principles

1. **Performance over Precision**: Use linear heuristics (Expected Value) inside MCTS loops rather than exact combinatorial math (Hypergeometric) to maximize tree search throughput.
2. **State Representation (Start from Zero)**:
   - Cards are represented as **Rich Feature Vectors**: costs, attributes, and hearts.
   - Abilities are represented as **Bytecode Sequences**: Feed the raw bytecode instructions (opcodes/params) into the transformer so the AI learns the "programming" of the cards without human bias.
   - **Card Counting**: Enable perfect card counting by passing discard/hand/stage histograms, allowing the network to infer the remaining deck composition.
3. **Hybrid Solvers & Meta-Heuristics**: Use the transformer to dynamically predict weight parameters for standard linear heuristics, combining deep strategic intuition with blazing-fast analytical math.

## Workflow

1. **Analytical Baseline**: Verify engine logic using `test_performance_solver.rs`.
2. **Heuristic Profiling**: Measure the throughput of the analysis layer to ensure it doesn't bottleneck MCTS.
3. **Data Collection**: Export game traces where the analytical solver provides "ground truth" labels for success probability.
4. **Automated Evaluation**: Use `ai_tournament.py` to benchmark agent performance against a baseline (e.g., `OriginalHeuristic`) across a variety of decks to ensure no regressions in strategy.

## Evaluation & Benchmarking

The consolidated tournament runner allows for high-performance auditing of AI agents.

### [ai_tournament.py](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/alphazero/benchmarks/ai_tournament.py)
This tool runs parallel matches using the Rust engine to evaluate heuristic or network performance.

**Standard Benchmark (Smoke Test)**:
```bash
uv run python alphazero/benchmarks/ai_tournament.py --sims 128 --games_per_pair 5
```

**High-Fidelity Audit**:
```bash
uv run python alphazero/benchmarks/ai_tournament.py --sims 4096 --games_per_pair 1 --p0_type original --p1_type original
```

**Matchup Configuration**:
- `--p0_type` / `--p1_type`: `original`, `legacy`, `simple`.
- `--sims`: Number of MCTS simulations per move.
- `--decks`: Optional list of specific deck files.

## Performance Benchmarks
As of recent optimizations (Action Generation pre-caching, Bytecode sharing with `Arc`, and `match`-based dispatch):
- **Single-Threaded**: ~137k steps/sec
- **Multi-Threaded (12t)**: ~577k - 640k steps/sec
*The engine maintains >100k steps/sec per thread, exceeding the minimum MCTS requirement.*

## Implementation Notes
- **Bytecode Sharing**: Execution frames use `Arc<Vec<i32>>` for zero-copy bytecode sharing across branching/remote triggers.
- **Opcode Dispatch**: Uses a central `match` jump table in `handlers/mod.rs` for O(1) instruction routing.
- **Inlining**: Hot path functions (`calculate_proximity`, `process_hearts`) are marked with `#[inline]` to reduce call overhead.

## Stability & Numerical Safety

1.  **Illegal Action Masking**: Mask illegal actions directly in the network's forward pass before the final `log_softmax`. Use a large negative number (e.g., `-1e10`) for masked values.
2.  **Loss Function Stability**: Prefer PyTorch's `F.cross_entropy` over manual implementation of cross-entropy to handle logarithmic stability internally.
3.  **Anomaly Detection**: During development, use `torch.autograd.set_detect_anomaly(True)` to trace `NaN` gradients back to their source.

## Observability & Logging

1.  **Action Enrichment**: Self-play logs (`alphazero_game_log.txt`) should include card IDs and names for readability.
2.  **MCTS Transparency**: Always log the legal action list, visit counts, and win-rate scores (Q-values) for each move to audit tree search quality.
3.  **State Dumps**: At the end of each game, generate a comprehensive state report (Bug Report JSON) using the engine's serialization logic for post-mortem analysis.

## Resources
- [MCTS Performance Principles](resources/mcts_performance_principles.md)
- `engine_rust_src/src/core/analysis/performance_solver.rs` (Implementation Reference)
