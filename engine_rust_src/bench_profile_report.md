# Engine Throughput Benchmark Report

## Summary

This report captures the recent profiling and benchmark work in `engine_rust_src`.

### What changed

- `src/core/logic/action_gen/main_phase.rs`
  - Updated internal profile timing from integer microseconds to floating-point microseconds.
  - Profile output now prints decimal microseconds using `{:.2}` formatting.
  - Reduced heap allocation in OnPlay choice handling by replacing a temporary `Vec<i32>` with a fixed-size `[i32; 6]` stack buffer.

- `examples/bench_profile_legal_actions.rs`
  - Switched legal-action storage from `SmallVec<[i32; 64]>` to `Vec<i32>` to avoid `ActionReceiver` trait mismatches caused by duplicate `smallvec` versions in the dependency graph.
  - Confirmed the profiling harness still builds and executes.

- `examples/bench_throughput.rs`
  - No source changes were required for this run.
  - This benchmark is the correct raw engine-speed harness for throughput measurement.

## Why this matters

- `bench_profile_legal_actions.rs` is a trace-oriented profiler that prints step-by-step game state, debug logs, and profiling lines. It is not intended for clean throughput reporting.
- `bench_throughput.rs` is the right benchmark for raw engine performance numbers.
- The recent code updates ensure the profiler output is accurate, while the throughput benchmark remains the correct raw measurement tool.

## Run command

Clean 8-worker benchmark command from `engine_rust_src`:

```powershell
$env:BENCH_GAMES='1000'
$env:BENCH_WARMUP_GAMES='0'
$env:BENCH_WORKERS='8'
$env:BENCH_MAX_STEPS='10000'
$env:BENCH_DEBUG_MODE='0'
$env:BENCH_PROFILE_LEGAL_ACTIONS='0'
$env:BENCH_TRACE_FIRST_GAME='0'
cargo run --release --manifest-path .\Cargo.toml --bin bench_throughput
```

## Latest results

- Games: `1000`
- Terminal: `1000` (P0=547, P1=453, Draw=0)
- Total steps: `230751`
- Avg steps/game: `230`
- Time per game: `2138μs`
- Time per step: `9266ns`
- Throughput:
  - `3644` games/sec
  - `840928` steps/sec
- Total benchmark time: `274ms`

## Notes

- `bench_throughput.rs` is the raw throughput benchmark and should be run without debug/profile/tracing flags for clean numbers.
- The earlier single-worker run was slower because it was limited to `BENCH_WORKERS=1` and still had debug/profile state in the environment.
- The 8-worker run recovers the expected high throughput and is the correct comparative metric for engine speed.
