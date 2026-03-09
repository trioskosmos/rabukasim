# Overengineering Analysis: RabukaSim Rust Engine

This document outlines areas of the codebase identified as potentially overengineered relative to the requirements of the project.

## 1. Dual-Stack Implementation (Rust & WGSL)

The most significant source of complexity is the parallel implementation of game logic in both Rust (`engine_rust_src/src/core/logic/`) and WGSL shaders (`engine_rust_src/src/core/shader_*.wgsl`).

### Findings
- **Code Duplication:** Almost every core mechanic, opcode, and condition must be implemented twice: once in Rust for CPU execution/validation and again in WGSL for GPU-accelerated MCTS rollouts.
- **Synchronization Burden:** The `tools/verify_wgsl_rust_sync.py` script attempts to keep these in sync, but manual intervention is often required (e.g., struct padding, alignment).
- **Complexity vs Benefit:** For a card game with a relatively small state space compared to board games like Go or Chess, the overhead of maintaining a custom GPU compute kernel likely outweighs the performance benefits over a highly optimized CPU implementation, especially given the maintenance cost of debugging shader logic.
- **Memory Layout Rigidity:** The need for `#[repr(C)]` and manual padding in `gpu_state.rs` to match WGSL alignment rules adds friction to changing game state structures.

## 2. Inefficient Telemetry Logging

The interpreter includes a logging mechanism that appears to be debug-oriented but is integrated into the core execution loop in a way that could severely impact performance if enabled or left in production code paths.

### Findings
- **Blocking I/O:** `src/core/logic/interpreter/mod.rs` contains `log_opcode_to_file`, which opens, writes to, and closes a file (`reports/telemetry_raw.log`) for *every single opcode executed*.
- **Global Locking:** The use of `GLOBAL_OPCODE_TRACKER` with a `Mutex` introduces contention in what should be a highly parallelizable MCTS environment.

## 3. Interpreter Architecture

The bytecode interpreter is designed with a stack-based architecture (`BytecodeExecutor`, `ExecutionFrame`) capable of handling deep recursion and complex control flow.

### Findings
- **Recursion Depth:** The `MAX_DEPTH` is set to 8, which is reasonable, but the manual stack management for `ExecutionFrame` adds complexity.
- **Opcode Granularity:** The opcode set includes very low-level operations (jumps, extensive condition codes) mixed with high-level game logic. This hybrid approach makes the interpreter complex to maintain and optimize.
