# LOVECA Engine Benchmarks

This directory contains the canonical performance benchmark for the LOVECA card game engine.

## Canonical Benchmark

### `ultimate_benchmark.rs`
Headless full-game stress benchmark that:

- uses `cards_compiled.json` with abilities enabled
- initializes games through the normal engine path with seeded shuffles
- plays only by choosing random legal actions
- runs in silent/headless mode so timing is engine-heavy, not log-heavy
- samples many random deck combinations like the frontend init path
- records slow action/phase timings and repeated-state soft-lock fingerprints

This is intentionally the only active bench target. Older split bench files remain in the repo as reference material, but Cargo now points to the unified benchmark harness.

## What It Reports

- total games, terminal games, capped games, and stalled games
- games per second and actions per second
- time spent in legal-action generation, chosen-action execution, and auto-step fallback
- the slowest board states seen during the run
- repeated-state fingerprints that look like soft locks or non-progress loops

## Running The Benchmark

### Default run
```bash
cargo bench --bench ultimate_benchmark
```

### Common tuning knobs
```bash
BENCH_SECS=20 BENCH_MAX_STEPS=8000 BENCH_SLOW_US=500 cargo bench --bench ultimate_benchmark
```

Supported environment variables:

- `BENCH_SECS`: wall-clock benchmark duration
- `BENCH_WARMUP_GAMES`: number of untimed warmup games
- `BENCH_MAX_STEPS`: per-game hard cap before declaring a cap
- `BENCH_SLOW_US`: threshold for printing a slow event
- `BENCH_REPEAT_LIMIT`: repeated-state visit threshold for declaring a stall
- `BENCH_SAME_STATE_LIMIT`: consecutive identical-state threshold for declaring a stall
- `BENCH_SEED`: base RNG seed

## Notes

- This harness uses random legal actions only. It does not call TurnSequencer or MCTS.
- Because the workspace rulebook text file is not currently present under `docs/rules/rules.txt`, setup fidelity is taken from the real engine initialization path and the frontend WASM init flow.

Prefer changing this harness rather than adding another standalone benchmark target.
