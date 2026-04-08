# Ability Data Flow

This folder contains both authored inputs and generated outputs. The important distinction is:

- `data/ability_frame_source.json` is the authored sparse source / manifest-style input.
- `data/cards_compiled.json` is the compiled card database that actually stores per-card `abilities[].frame_program.frames[]`.
- `data/ability_runtime_index.json` is the machine-facing runtime hydration index used by Rust and code generation.
- `data/ability_frame_index.json` is the human-facing review index.

Build flow:

1. The compiler reads `data/cards.json` as the raw card database.
2. It reads `data/ability_frame_source.json` as the authored sparse ability input.
3. It compiles those sources into `data/cards_compiled.json`.
4. The build pipeline then refreshes the runtime and review indexes and mirrors compiled artifacts where needed.

Important note:

- If you are looking for actual per-card frame data such as `ADD_HEARTS`, inspect `data/cards_compiled.json`, not `data/ability_frame_source.json`.
- `data/ability_frame_source.json` is upstream input, but it is not the place where the fully materialized per-card `frame_program.frames[]` lives.

Current behavior:

- Rust reopens `data/ability_runtime_index.json` at load time to reattach executable frames onto the semantic card export.

Related files:

- `data/ability_frame_source.json` for authored sparse ability input
- `data/ability_runtime_index.json` for machine-facing runtime hydration
- `data/ability_frame_index.json` for review-friendly inspection
- `data/cards_compiled.json` for compiled runtime output and per-card frame programs
- `data/metadata.json` for opcode ids and packed layout schema
- `engine/data/cards_compiled.json` for the engine-side live mirror
- `launcher/static_content/data/cards_compiled.json` for the launcher-side live mirror
- `engine_rust_src/src/core/logic/card_db.rs` for the runtime loader
- `docs/plans/ability_pipeline_code_audit.md` for the current code-derived pipeline audit
