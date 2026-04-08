# Search Harness Commands

This directory contains standalone binaries for engine diagnostics and search runs.

## Fastest Terminal Turn Search

`search_fastest_terminal_turn.rs` runs full games, keeps the starting deck order fixed by seed, varies the action seed per game, and prints a record line every time it finds a lower terminal turn count.

Use it like this:

```bash
# Run a large search with the default fixed deck seed and derived action seeds.
BENCH_GAMES=4000 BENCH_WORKERS=8 cargo run --release --manifest-path engine_rust_src/Cargo.toml --bin search_fastest_terminal_turn

# Force the exact same starting deck order and action seed baseline on every run.
BENCH_GAMES=4000 BENCH_WORKERS=8 BENCH_DECK_SEED=0 BENCH_ACTION_SEED=0 cargo run --release --manifest-path engine_rust_src/Cargo.toml --bin search_fastest_terminal_turn

# Use a smaller debug run when you only want to verify the harness wiring.
BENCH_GAMES=2 BENCH_WORKERS=1 BENCH_DECK_SEED=0 BENCH_ACTION_SEED=0 cargo run --manifest-path engine_rust_src/Cargo.toml --bin search_fastest_terminal_turn
```

Environment variables:

- `BENCH_GAMES`: total games to run
- `BENCH_WARMUP_GAMES`: warmup games that are not counted in the summary
- `BENCH_WORKERS`: worker threads for parallel runs
- `BENCH_MAX_STEPS`: per-game hard step cap
- `BENCH_DECK_SEED`: fixed seed for the starting deck order
- `BENCH_ACTION_SEED`: base seed used to derive each game's action RNG

The terminal condition is a real game end: a player has 3 or more cards in `success_lives`.