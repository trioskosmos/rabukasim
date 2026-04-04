# Ability Data Flow

`data/ability_frame_index.json` is the single authored and runtime ability index.

- Runtime code reads `data/ability_frame_index.json` for frame-program lookup.
- The compiler reads the same file for authored sparse ability data.
- `data/cards_compiled.json` remains the compiled card database.
- The build pipeline validates and mirrors runtime artifacts; it does not rebuild a second ability source file.

Related files:

- `data/manual_pseudocode.json` for explicit overrides
- `data/ability_frame_index.json` for shared authored/runtime sparse ability data
- `data/cards_compiled.json` for compiled runtime output
- `engine/data/cards_compiled.json` for the engine-side live mirror
- `launcher/static_content/data/cards_compiled.json` for the launcher-side live mirror
- `engine_rust_src/src/core/logic/card_db.rs` for the loader that consumes this
  index
