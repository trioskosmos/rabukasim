# LOVECA Engine Benchmarks

This directory documents the benchmark files that still exist in the workspace and marks which one should be used for raw engine throughput.

## Current Benchmark

### `../examples/bench_throughput.rs`
This is the current raw speed benchmark for the engine. It:

- runs headless and silent
- starts real games through the normal engine initialization path
- plays only random legal actions or auto-step transitions
- can run multiple independent games across worker threads
- can optionally trace one game so you can verify it is really playing
- reports terminal vs capped games, wall-clock games/sec, and wall-clock steps/sec

On the 12-core machine used for the latest sweep, 8 workers was the best measured setting for this harness. 12 workers still scaled, but it was slower than 8, so treat 8 as the practical default sweet spot unless you remeasure on different hardware.

Use this benchmark when you want raw engine throughput, step rate, or thread-scaling data.

### `../examples/bench_pass_action.rs`
This is a new pass-only benchmark for the engine. It:

- runs a tight loop of `step_internal(ACTION_BASE_PASS)` plus `auto_step`
- measures the pass-only engine path without random legal-action selection
- reports per-pass latency and the split between `step_internal` and `auto_step`
- is useful when you want to profile engine overhead for the common pass/auto-step loop

Use this benchmark when you need a microbenchmark for the pass-only path rather than full-game random-action throughput.

Example run:

```bash
cargo run --release --manifest-path engine_rust_src/Cargo.toml --bin bench_pass_action
```

Example runs:

```bash
cargo run --release --manifest-path engine_rust_src/Cargo.toml --bin bench_throughput
BENCH_GAMES=4000 BENCH_WORKERS=12 BENCH_MAX_STEPS=10000 cargo run --release --manifest-path engine_rust_src/Cargo.toml --bin bench_throughput
BENCH_TRACE_FIRST_GAME=1 BENCH_GAMES=1 cargo run --release --manifest-path engine_rust_src/Cargo.toml --bin bench_throughput
BENCH_DEBUG_MODE=1 BENCH_PROFILE_LEGAL_ACTIONS=1 BENCH_PROFILE_TRIGGERS=1 BENCH_PROFILE_PLAY_MEMBER=1 BENCH_PROFILE_STEP_THRESHOLD_US=100 cargo run --release --manifest-path engine_rust_src/Cargo.toml --bin bench_throughput
```

By default the benchmark now uses up to 8 workers, capped by the machine's available parallelism.

Supported environment variables:

- `BENCH_GAMES`: number of games to run
- `BENCH_WARMUP_GAMES`: untimed warmup games
- `BENCH_WORKERS`: number of worker threads used for independent games
- `BENCH_MAX_STEPS`: hard step cap per game, default `10000`
- `BENCH_SEED`: base RNG seed
- `BENCH_TRACE_FIRST_GAME`: print a trace for the first game when set to `1`, `true`, `yes`, or `on`
- `BENCH_TRACE_STEP_LIMIT`: number of trace steps printed for the traced game
- `BENCH_DEBUG_MODE`: enable internal debug-mode profiling output when combined with profiling env vars

## Deprecated Or Diagnostic Benchmarks

These files still exist, but they are not the raw throughput benchmark.

| File | Status | What it does | Typical use |
| --- | --- | --- | --- |
| `ultimate_benchmark.rs` | Diagnostic | Full-game random-legal-action stress benchmark with detailed slow-state, residual, and fingerprint reporting | Use when you need forensic timing data for a pathological state |
| `bench_granular_v2.rs` | Diagnostic | Granular full-game benchmark that breaks time into planning, execution, auto-step, and state patterns | Use for phase attribution and slow-state clustering |
| `bench_granular_real.rs` | Diagnostic | Similar granular benchmark that follows a more frontend-like turn planning path | Use when comparing planner-heavy real-game flow |
| `bench_diagnostic.rs` | Diagnostic | Ultra-granular timing and board-state tracer for a focused call path | Use for card/opcode or board-shape debugging |
| `bench_deterministic.rs` | Diagnostic | Records and replays exact action sequences for repeatability checks | Use when verifying determinism or replay stability |
| `bench_fast.rs` | Legacy | Older fast throughput demo with simplified deck loading and hard-coded limits | Use only as a historical reference |

If you are measuring raw engine speed, prefer `bench_throughput.rs`. If you are chasing a specific slow fingerprint, use `ultimate_benchmark.rs` or `bench_granular_v2.rs`.

## Notes

- The raw throughput benchmark uses random legal actions only. It does not call TurnSequencer or MCTS.
- The game is real: the benchmark stops only when `state.is_terminal()` becomes true or the step cap is hit.
- A terminal game means one player reached 3 cards in `success_lives`.
- For the slow-state investigation workflow, see [`docs/plans/ultimate_benchmark_slow_state_workflow.md`](../../docs/plans/ultimate_benchmark_slow_state_workflow.md).

Prefer changing the raw throughput benchmark before adding another standalone speed test.
