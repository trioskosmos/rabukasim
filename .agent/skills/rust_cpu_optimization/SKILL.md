# Rust CPU Optimization Skill

This skill provides a set of guidelines and best practices for optimizing the Rust-based game engine for maximum CPU performance, especially for MCTS (Monte Carlo Tree Search) and simulation rollouts.

## 🚀 Optimization Strategies

### A. Compiler & Cargo Optimizations (The "Free" Speedups)
Standard release profiles are often optimized for a balance of compile time and speed. For production/benchmark runs, use maximum optimization:

**Cargo.toml [profile.release]**
```toml
[profile.release]
lto = "fat"          # Enable Link-Time Optimization (Huge performance boost, slow compile)
codegen-units = 1    # Allows LLVM to optimize across the entire crate
panic = 'abort'      # Removes unwinding overhead
opt-level = 3
```

**Target Native CPU**
Always run benchmarks and release builds with the native CPU target to enable vectorized instructions (AVX2/AVX-512):
```bash
RUSTFLAGS="-C target-cpu=native" cargo build --release
```

### B. Memory Allocation (The Biggest Bottleneck)
Dynamic memory allocation (`malloc`/`free`) is expensive in tight loops.

1.  **Use Arenas**: Pre-allocate memory on startup and use an arena allocator (like `bumpalo`) instead of individual `Vec::new` or `Box::new` calls within the simulation loop.
2.  **SmallVec**: Use `SmallVec<[u16; 10]>` instead of `Vec<u16>` for small, bounded collections (like targets or zones) to keep data on the stack.

### C. Data Structures & Cache Locality
Optimize for CPU cache behavior.

1.  **Bitboards**: Represent zones as `u64` bitmasks where possible. Set operations (intersections, target finding) become single CPU instructions.
2.  **Struct of Arrays (SoA)**: If iterating over many entities, consider splitting a large `Vec<GameState>` into multiple arrays of primitive types to improve L1/L2 cache utilization.

### D. Pruning the State Machine
1.  **Minimize Cloning**: Avoid `clone()` in simulation stacks. Use Copy-on-Write (`Cow`) or persistent data structures (e.g., the `im` crate) to share memory between nodes in the search tree.
2.  **Efficient State Management**: Ensure state transitions are lean and do not trigger unnecessary logic recalculations.

### E. Benchmarking & Profiling
To verify the impact of optimizations, use the unified Rust benchmark tool:

```bash
cd engine_rust_src
cargo run --release --bin benchmark_unified
```

This benchmark runs a 10-second simulation challenge, reporting games per second and steps per second for both single-threaded and multi-threaded execution.
