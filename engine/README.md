# Legacy Python Engine

> [!WARNING]
> **This directory is RETIRED and should be considered LEGACY.**
> All active development and logic execution for the LovecaSim engine must happen in `engine_rust_src/`.

### Why is this folder still here?
The `compiler/` tool still relies on `engine.models` for certain data structures and type definitions during the `data/cards.json` -> `data/cards_compiled.json` compilation process.

### What should I NOT do?
- **DO NOT** edit code in `engine/game/` or `engine/logic/` and expect it to affect the game.
- **DO NOT** add new features to the Python implementation.
- **DO NOT** rely on this engine for production-level card behavior verification.

### What should I do?
- **ONLY** modify `engine/models/ability.py` if it's necessary to update the schema for the Rust engine's bytecode.
- All engine logic changes belong in `engine_rust_src/`.
