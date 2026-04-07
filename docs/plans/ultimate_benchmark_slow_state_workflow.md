# Ultimate Benchmark Slow-State Workflow

This note explains how to run `ultimate_benchmark.rs` and how to use its slow-state output to find and fix expensive board states.

It is a process note, not a results log. The goal is to make the benchmark useful as a repeatable debugging tool.

## What The Benchmark Is For

`ultimate_benchmark.rs` is the canonical headless stress benchmark for the Rust engine.

It is useful for three separate questions:

1. Does the engine finish games cleanly?
2. Which phases or actions are expensive?
3. Which exact board states trigger the worst spikes?

It is not a replacement for targeted tests. It is a way to find real runtime hotspots that only show up once the engine is exercised at scale.

## How To Run It

Default run:

```bash
cargo bench --bench ultimate_benchmark
```

Useful tuning knobs:

```bash
BENCH_SECS=20 BENCH_MAX_STEPS=8000 BENCH_SLOW_US=500 cargo bench --bench ultimate_benchmark
```

Common environment variables:

- `BENCH_SECS`: total wall-clock duration
- `BENCH_WARMUP_GAMES`: untimed warmup games before recording
- `BENCH_MAX_STEPS`: hard per-game safety cap
- `BENCH_SLOW_US`: threshold for recording a slow event
- `BENCH_REPEAT_LIMIT`: repeated-state limit before a stall is reported
- `BENCH_SAME_STATE_LIMIT`: consecutive identical-state limit before a stall is reported
- `BENCH_SEED`: base RNG seed

For pure performance investigation, it is often useful to temporarily raise the stall limits so the benchmark can keep exploring longer games:

```bash
BENCH_REPEAT_LIMIT=1000000 BENCH_SAME_STATE_LIMIT=1000000 cargo bench --bench ultimate_benchmark
```

That does not change the engine rules. It only changes when the benchmark decides to stop early.

## How To Read The Output

The benchmark output has two different kinds of signals:

### Summary counters

These tell you whether the engine is finishing games and whether it is making progress.

Watch for:

- `terminal`: games that ended normally
- `stalled`: games that repeated states too often
- `capped`: games that hit the step cap
- `step_errors`: actions that failed inside the engine
- `real_no_progress_events`: non-pass actions that left the state unchanged
- `benign_pass_loops`: legal passes that did not advance the state

The important distinction is between a real engine problem and a legal no-op:

- a legal pass loop can be expected in optional prompt states
- a `step_error` or `real_no_progress_event` usually means the engine is rejecting a meaningful action and should be investigated

### Slow-state tables

The slow-state tables are the main tool for optimization work.

They show:

- the operation type
- the phase where the cost happened
- the board snapshot
- the slowest example observed for that state

The snapshot is the part that matters most. It tells you which exact board shape is expensive, not just which phase is expensive in general.

For `StepMain` and `StepResponse`, raw `max_us` is not enough on its own. Some "slow step" entries are mostly paying for prompt setup or response-action materialization, not for a large gameplay transformation. Always ask how much board state actually changed during that time before optimizing the wrong layer.

## How To Turn A Slow State Into A Fix

Use the following loop:

1. Find the slowest `LegalActions` or `Step` entry.
2. Note the phase and the snapshot fields.
3. Identify the code path that handles that phase.
4. Trace the expensive helper calls inside that path.
5. Check whether the work is repeated per candidate action, per card, or per interaction.
6. Remove duplicated scans, cache stable per-pass facts, or replace full-state copies with narrow projections.
7. Rerun the benchmark and look for the same state again.

The most useful question is usually not "is this phase slow?" but "what is being recomputed for every action in this board shape?"

## What To Inspect First

In practice, the slow states usually map to a small set of hotspots:

- `LegalActionsMain`
  - start in `engine_rust_src/src/core/logic/action_gen/main_phase.rs`
  - inspect per-card legality checks, condition checks, cost checks, and aura projection
- `StepMain`
  - start in `engine_rust_src/src/core/logic/handlers.rs`
  - inspect trigger dispatch, rule checks, forced state maintenance, and whether the step eagerly materializes the next prompt's action list
- `StepResponse`
  - start in `engine_rust_src/src/core/logic/handlers.rs`
  - inspect prompt resume logic, selection recovery, response handlers, and duplicate legal-action generation for already-materialized prompts
- `StepLiveSet`
  - start in `engine_rust_src/src/core/logic/handlers.rs` and `engine_rust_src/src/core/logic/game_trigger.rs`
  - inspect draw, cleanup, aura/stat sync, and trigger fan-out

If the slow state repeats in the same phase, inspect that phase first. Do not start by changing the benchmark harness unless the output itself is misleading.

## How To Tell If A State Is Worth Fixing

Not every slow state deserves a code change.

Good candidates usually have one or more of these traits:

- the same board shape appears many times
- the slow work happens inside an inner loop
- the expensive call is repeated for each candidate move
- a full-state clone or full-board scan is obvious in the call path
- the work is stable enough to cache for the duration of one legality or step pass

Less interesting cases usually look like this:

- a single rare spike in a complex but valid endgame
- a legal optional pass state
- a one-off response window with many prompts already resolved

## Investigation Pattern That Has Worked Best

The most productive pattern has been:

1. Run the benchmark with slow-state logging enabled.
2. Sort by operation and max duration.
3. Pick the largest recurring `LegalActionsMain` or `StepMain` state.
4. Open the phase handler or action generator for that state.
5. Look for repeated scans, repeated aura calculations, repeated frame walks, or full-state copies.
6. Replace the repeated work with cached per-pass data or a narrower helper.
7. Re-run the benchmark and repeat.

This has been more effective than trying to optimize "the engine" as a whole.

## Good Optimization Targets

The kinds of fixes that tend to pay off are:

- replacing `clone()` on large runtime state with a projection helper
- caching results that are stable for the current legality pass
- avoiding repeated per-card scans when the answer can be derived from zone lengths or precomputed metadata
- narrowing condition checks so they do not walk the same structures several times
- separating benign pass loops from real no-progress failures

## What Not To Do

Avoid these traps:

- do not optimize based only on total game duration
- do not assume a stall means the engine is broken
- do not assume a slow `Step` means one handler is expensive by itself
- do not change the benchmark thresholds before understanding whether the state is a real bug or just a legal loop
- do not add new benchmark targets unless this harness truly cannot express the question you are asking

## Reproduction Checklist

When making a change, the shortest useful verification loop is:

1. run the benchmark
2. inspect the slow-state table
3. make one targeted change
4. rerun the benchmark
5. confirm that the same state no longer dominates
6. run the relevant focused tests if the change touched prompt or response behavior

That keeps the benchmark anchored to a specific runtime question instead of turning into a generic timing run.
