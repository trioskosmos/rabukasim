# LOVECA Engine Benchmarks

This directory contains performance benchmarks for the LOVECA card game engine using Criterion.rs.

## Available Benchmarks

### `game_simulation.rs`
Full-game benchmarks that run complete AI vs AI matches at full speed.

- **`full_game_simulation/vanilla_ai_vs_ai`** - Complete game from start to finish
- **`game_phases/game_initialization`** - Time to initialize a new game state
- **`game_phases/auto_step_through_mulligan`** - Auto-step through mulligan phase
- **`batch_simulation/games/5`** - Batch of 5 games
- **`batch_simulation/games/10`** - Batch of 10 games
- **`batch_simulation/games/25`** - Batch of 25 games

### `engine_components.rs`
Low-level component benchmarks for core engine operations.

- **`card_filter/character_filter_100_cards`** - Character filtering across 100 cards
- **`card_filter/filter_1000_iterations`** - Filter stress test with 1000 iterations
- **`game_state_operations/clone_full_game_state`** - Game state cloning
- **`game_state_operations/get_legal_actions_initial`** - Legal action generation
- **`database/create_card_database`** - Database initialization
- **`database/card_lookup_by_id`** - Card lookup performance

### `turn_sequencer.rs`
Turn sequencing and AI search benchmarks.

- **`turn_sequencer_main/find_best_main_sequence`** - Main phase action search
- **`turn_sequencer_liveset/find_best_liveset_selection`** - Liveset selection search
- **`sequencer_scaling/main_sequence/*`** - Scaling with game progress
- **`search_depth/heuristic_evaluation`** - Heuristic evaluation performance

### `micro_benchmarks.rs`
Nanosecond-level micro-benchmarks and slow move detection for identifying performance outliers.

- **`slow_move_detector/batch_100_games_with_timing`** - Runs 100 games and statistically identifies slow operations
  - Reports operations taking >100μs
  - Shows min/avg/max timing per phase
  - Flags operations exceeding 1ms
- **`micro_operations/single_step`** - Time for a single game step (nanoseconds)
- **`micro_operations/get_legal_actions`** - Legal action generation (nanoseconds)
- **`micro_operations/auto_step`** - Auto-step execution (nanoseconds)
- **`micro_operations/find_best_main_sequence`** - AI search per step (nanoseconds)
- **`throughput/games_per_second`** - How many complete games per second

### Slow Move Detection

The `micro_benchmarks.rs` file contains a **slow move detector** that works by:
1. Running 100+ games at full speed
2. Recording timing for every operation
3. Statistical analysis to find outliers
4. Reporting operations that exceed thresholds (100μs, 1ms)

This detects slow operations even without specific strategies - they show up as statistical outliers.

## Running Benchmarks

### Run all benchmarks
```bash
cargo bench
```

### Run specific benchmark
```bash
cargo bench --bench game_simulation
cargo bench --bench engine_components
cargo bench --bench turn_sequencer
```

### Run with release profile (recommended for accurate results)
```bash
cargo bench --release
```

### Filter benchmarks by name
```bash
cargo bench game_simulation
cargo bench card_filter
cargo bench sequencer
```

## Viewing Results

After running, Criterion generates HTML reports in:
```
target/criterion/
```

Open `target/criterion/report/index.html` in a browser for interactive charts.

## Interpreting Results

- **Time per iteration** - Lower is better
- **Throughput** - Higher is better (operations per second)
- **Slope in change** graphs - Watch for performance regressions
- **Warmup** - First run may be slower due to JIT/cache warming

## Performance Tuning Tips

1. Always run benchmarks on release builds: `cargo bench --release`
2. Close other applications to reduce noise
3. Run multiple times to verify consistency
4. Use `criterion::black_box()` to prevent compiler optimizations
5. Benchmark incremental changes to measure impact

## Adding New Benchmarks

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn my_benchmark(c: &mut Criterion) {
    c.bench_function("my_function", |b| {
        b.iter(|| {
            black_box(my_function());
        });
    });
}

criterion_group!(benches, my_benchmark);
criterion_main!(benches);
```
