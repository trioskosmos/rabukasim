---
name: future_implementations
description: A registry of planned but deferred features, optimizations, and architectural improvements for the LovecaSim engine.
---

# Future Implementations

This skill tracks technical debt, missing features, and optimization opportunities that are out of scope for current tasks but critical for long-term project health.

## 1. AI Observation Space Gap (Critical for RL)
**Problem**: The current `encode_state` function in `src/core/logic/game.rs` provides the AI with:
-   Hand Cards
-   Stage Cards
-   Live Zone Cards
-   Deck Counts / Scores

However, it **DOES NOT** encode `looked_cards`.
**Impact**: When the AI triggers `looked_cards` (via `O_LOOK_AND_CHOOSE` or `O_SEARCH_DECK` or `O_RECOV_L`), it receives a list of legal actions (e.g., "Pick Option 0", "Pick Option 1") but has **zero information** about what cards are at those indices. The AI is effectively blind during these choices.

**Proposed Solution**:
1.  Expand the observation vector size in `game.rs`.
2.  Reserve a fixed block (e.g., 5-10 slots) for "Temporary/Looked Zone" features.
3.  Populate this block only when `Phase == Response` and `looked_cards` is not empty.
4.  Ensure `v_remaining` is also encoded so the AI knows how many more picks it needs to make.

## 2. Dynamic Action Space Sizing
**Problem**: We currently use a fixed 12,000 action space.
**Proposal**: Investigate if we can mask invalid actions more efficiently at the Python binding level to speed up training.

## 3. Advanced Heuristics
**Problem**: `OriginalHeuristic` is a holistic evaluation but computationally expensive.
**Proposal**: Implement `LightweightHeuristic` for faster MCTS rollouts.

## 4. Temporary Buff/Heart Cleanup (Dissipation)
**Problem**: Some abilities provide "Until end of live" or "This turn" hearts/blades.
**Requirement**: Explicitly verify that these buffs are cleared correctly at the end of their respective durations (e.g., in `untap_all` or phase transitions).
**Impact**: Preventing state leakage across rounds is game-critical.

## 5. Test Suite Unification
**Problem**: Test action IDs often drift from engine constants.
**Proposal**: Use `ACTION_BASE_*` constants in helper enums.

## 6. MCTS Performance Prediction: i32 IDs
**Claim**: Global migration to `i32` for card IDs has **zero negative impact** on MCTS rollout speed or memory efficiency.
**Supporting Arguments**:
- **Alignment**: Rust's `SmallVec` and structs often include padding to 4-byte boundaries. `i32` utilizes this space effectively.
- **Sentinel Efficiency**: CPU branch predictors find `if id >= 0` easier than `Option::is_some` discriminant tags.
- **Memory Math**: Adding ~1KB per `GameState` is negligible for modern RAM throughput (50GB/s+).
**Status**: Record created Feb 17, 2026. Future sessions should benchmark if MCTS bottlenecks occur.

## 7. GPU MCTS Optimization Registry
The current GPU implementation (RTX 3050 Ti) achieves ~835k sims/sec. Significant performance is left on the table due to PCIe bottlenecks and synchronization.

### 7.1 Score-Only Readback (High Priority)
**Problem**: We download the full 1280-byte state back to the CPU, even though MCTS only needs a single evaluation score.
**Improvement**: Add a dedicated `f32` results buffer. Download 4 bytes per state instead of 1280 (320x reduction in download bandwidth).

### 7.2 State Trimming
**Problem**: `GpuGameState` (1280 bytes) contains fields unused during rollouts.
**Improvement**: Shrink state to ~400-600 bytes. This cuts upload PCIe transfer time by ~50%.

### 7.3 Double-Buffered Pipelining
**Problem**: The CPU/GPU work sequentially, leading to ~100ms of idle time per 10x10k batch.
**Improvement**: Use two sets of buffers to overlap [Upload N+1] with [Compute N] and [Download N-1].

### 7.4 Workgroup Tuning
**Problem**: Workgroup size 64 may under-utilize RTX 30-series SMs.
**Improvement**: Test workgroup sizes of 128 and 256.

### 7.5 Persistent Tree States
**Problem**: Game state is uploaded from scratch for every leaf evaluation.
**Improvement**: Keep state resident on GPU throughout the MCTS search process, only updating "forced actions" and reading back scores.

## 8. GPU Testing Viability & Parity Improvements
**Problem**: We investigated whether we could port Rust `#[test]` functions directly to WGSL to test GPU logic.
**Finding**: **Not viable**. WGSL lacks a test framework, assertions, and stdout. Interpreting pass/fail requires writing full GPU-to-CPU host code, which is exactly what our current CPU↔GPU parity testing pattern already does.
**Action Plan (Ordered Priorities)**:
1. **Shader Compile Smoke Test**: Add a simple `#[test]` in Rust to verify `GpuManager::new()` succeeds (catching basic WGSL syntax breaks).
2. **Convert Parity Binaries to Tests**: Migrate scenarios in `test_gpu_parity_suite.rs` into proper `#[test]` functions for CI integration and per-scenario failure reporting.
3. **Opcode Coverage Linting**: Write a structural validation test that ensures every compiled opcode in `cards_compiled.json` has a corresponding `case` block in `shader_rules.wgsl`.
4. **Statistical Parity Testing**: Run N=10,000 blind random rollouts on both CPU and GPU and assert that their average heuristic terminal scores stay within `ε`.
