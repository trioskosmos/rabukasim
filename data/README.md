# Ability Source of Truth

`data/consolidated_abilities.json` is the canonical authored source for ability
logic in this repository.

- Runtime code reads it to load card ability data.
- It should not be edited by engine code at runtime.
- Derived caches and compiled outputs live elsewhere.
- If the data needs regeneration, use the external data pipeline, not the
  runtime loader.

Related files:

- `data/manual_pseudocode.json` for explicit overrides
- `data/cards_compiled.json` for compiled runtime output
- `engine/data/cards_compiled.json` for the engine-side live mirror
- `launcher/static_content/data/cards_compiled.json` for the launcher-side live mirror
- `engine_rust_src/src/core/logic/card_db.rs` for the loader that consumes this
  file
