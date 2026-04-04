# Ability Data Flow

`data/ability_frame_index.json` is the single authored ability index.

- The compiler reads `data/ability_frame_index.json` as the authored sparse ability source.
- `data/cards_compiled.json` is the compiled runtime card database.
- The build pipeline validates the frame index and mirrors compiled runtime artifacts.

Current caveat:

- Rust still reopens `data/ability_frame_index.json` at load time to reattach executable frames onto the semantic card export. That is an active compatibility design, not the desired end state.

Related files:

- `data/ability_frame_index.json` for authored sparse ability data
- `data/cards_compiled.json` for compiled runtime output
- `data/metadata.json` for opcode ids and packed layout schema
- `engine/data/cards_compiled.json` for the engine-side live mirror
- `launcher/static_content/data/cards_compiled.json` for the launcher-side live mirror
- `engine_rust_src/src/core/logic/card_db.rs` for the runtime loader
- `docs/plans/ability_pipeline_code_audit.md` for the current code-derived pipeline audit
