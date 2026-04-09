# Legacy Python Engine

> [!WARNING]
> **This directory is legacy compatibility code.**
> All active engine logic and test execution live in `engine_rust_src/`.

### Why is this folder still here?
The `compiler/` and related tooling still depend on `engine.models` for shared schema and card data types while generating `data/cards_compiled.json`.

### What should I not do?
- **Do not** add new runtime gameplay logic to the Python engine.
- **Do not** treat the Python implementation as the source of truth for production card behavior.

### What should I do?
- **Only** modify `engine/models/ability.py` if the shared ability schema needs to change.
- Put engine logic changes in `engine_rust_src/`.
