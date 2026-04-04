# Ability Data Flow

The ability pipeline now uses three files with different roles.

- The compiler reads `data/ability_frame_source.json` as the authored sparse ability source.
- `data/ability_runtime_index.json` is the machine-facing runtime frame index used by Rust and code generation.
- `data/ability_frame_index.json` is the human-facing review index.
- `data/cards_compiled.json` is the compiled runtime card database.
- The build pipeline refreshes all three ability-index artifacts and mirrors compiled runtime artifacts.

Current behavior:

- Rust reopens `data/ability_runtime_index.json` at load time to reattach executable frames onto the semantic card export.

Related files:

- `data/ability_frame_source.json` for authored sparse ability data
- `data/ability_runtime_index.json` for machine-facing runtime hydration
- `data/ability_frame_index.json` for review-friendly inspection
- `data/cards_compiled.json` for compiled runtime output
- `data/metadata.json` for opcode ids and packed layout schema
- `engine/data/cards_compiled.json` for the engine-side live mirror
- `launcher/static_content/data/cards_compiled.json` for the launcher-side live mirror
- `engine_rust_src/src/core/logic/card_db.rs` for the runtime loader
- `docs/plans/ability_pipeline_code_audit.md` for the current code-derived pipeline audit
