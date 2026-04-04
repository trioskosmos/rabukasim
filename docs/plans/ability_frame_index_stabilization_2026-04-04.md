# Ability Frame Index Stabilization

## Goal
Create a durable base for `data/ability_frame_index.json` so new card waves can be added without manual JSON archaeology.

## Problems Addressed
- The frame index did not carry the actual authored Japanese ability text, so opcode sequences could not be audited against source text from the same artifact.
- Python-side inspection tooling still depended on stale handwritten opcode maps instead of `data/metadata.json`.
- The build pipeline validated the frame index but did not rewrite it from a deterministic normalized generator, which left the file drifting toward manual edits.

## Phase 1 Implemented
- `tools/frame_codec.py`
  - Enriches each ability entry with `primary_text_jp`, `primary_text_en`, and `source_ability_texts` derived from `data/cards_compiled.json`.
  - Emits a top-level `opcode_catalog` with used opcode/condition coverage and unknown-frame detection.
  - Tracks text coverage in `summary.text_covered_ability_count` and `summary.text_missing_ability_count`.
- `tools/abilities/pipeline.py`
  - Rebuilds `data/ability_frame_index.json` from normalized generator output instead of only stripping duplicate instruction keys.
- `tools/cf.py`
  - Resolves opcode and trigger names from `data/metadata.json` first, reducing drift in debugging output.

## What This Fixes Immediately
- Auditing a shared frame entry no longer requires opening three separate files just to compare opcode sequence to source text.
- Missing opcode names become visible at generation time through `opcode_catalog.unknown_entries`.
- The build path now converges the checked-in frame index toward one deterministic shape.

## Fallback And Hardcode Status
- Runtime cards now carry executable `frame_program`, so Rust no longer rehydrates sparse frames on the normal load path.
- Structured `card_refs` are emitted in the generated indexes so loaders do not have to recover identity from display labels first.
- The Rust runtime cleanup pass removed:
  - the `cid == 557` energy-count bypass
  - the `SELECT_MEMBER` structured fallback retry path
- Full Rust validation after those removals remained green.

## Remaining Runtime Debt
- Two source-card hardcodes still remain in Rust ability resolution for `4849` and `8844`.
- These are not being kept as endorsed compatibility behavior. They are compensating for authored/compiler gaps where the printed activated costs and branch structure are not yet fully represented in executable frames.
- The correct fix is upstream:
  - repair authored/source frame programs
  - regenerate runtime artifacts
  - delete the hardcoded interpreter branches

## Warning Status
- `cargo test --manifest-path engine_rust_src/Cargo.toml --no-run` currently emits no Rust compiler warnings in this cleanup slice.
- The expectation for follow-up cleanup is to keep that warning-free state while removing the remaining runtime compatibility code.

## Next Structural Step
- Split the current artifact into two layers if needed:
  - authored editable source
  - generated audit/runtime index
- If that split happens later, keep the current phase-1 fields and generator logic as the basis for the generated audit/runtime view.