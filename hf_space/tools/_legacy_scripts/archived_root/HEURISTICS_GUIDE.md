# Heuristics Maintenance Guide

This document explains the structure of the AI heuristics and how to modify them.

## File Structure

The AI logic is split across three main files in `engine_rust_src/src/core/`:

1.  **`heuristics.rs`**: Contains the **logic** for evaluating game states.
    *   `Heuristic` trait: The interface all heuristics must implement.
    *   `OriginalHeuristic`: The advanced evaluation logic (Hearts, Power, Proximity).
    *   `SimpleHeuristic`: A basic score-comparison evaluation.
2.  **`mcts.rs`**: The Monte Carlo Tree Search engine. It uses the heuristics to evaluate leaf nodes.
3.  **`logic.rs`**: The main game loop. It selects which heuristic to use based on configuration.

## How to Modify Heuristics

If you want to tweak the AI's intelligence (e.g., make it value "Yell" more):

1.  Open `engine_rust_src/src/core/heuristics.rs`.
2.  Modify the `evaluate_player` or `evaluate` method in `OriginalHeuristic`.
3.  **Recompile** the engine (see below).

## How to Add a New Heuristic

1.  Define a new struct in `heuristics.rs`:
    ```rust
    pub struct AggressiveHeuristic;
    impl Heuristic for AggressiveHeuristic { ... }
    ```
2.  Register it in `logic.rs` inside `play_mirror_match`:
    ```rust
    let h0: Box<dyn Heuristic> = match p0_heuristic_id {
        0 => Box::new(OriginalHeuristic),
        1 => Box::new(SimpleHeuristic),
        2 => Box::new(AggressiveHeuristic), // New!
        _ => ...
    };
    ```
3.  **Recompile**.

## Compilation

Because the logic is written in Rust, **changes do not take effect until you recompile.**

### For Python (Development/Testing)
Run this command in the root directory:
```bash
uv run maturin develop --release --manifest-path engine_rust_src/Cargo.toml
```

### For Offline Mode (WASM)
If you want the changes to appear in the browser version:
```bash
./scripts/build_dist.sh
```
*This will rebuild the WASM binary and package it into `dist/`.*
