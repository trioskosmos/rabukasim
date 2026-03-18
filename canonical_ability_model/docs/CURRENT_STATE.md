# Canonical Ability Model: Current State

This is the only canonical-ability documentation file that should be treated as current. Everything else in `canonical_ability_model/` is historical, archived, or implementation code.

## What We Have Today

- The authored canonical source is [`canonical_families.json`](../canonical_families.json).
- The card-by-card canonical draft is generated from that source at [`canonical_full_draft.json`](../drafts/canonical_full_draft.json).
- The current hybrid selection report is [`hybrid_runtime_preview.json`](../reports/hybrid_runtime_preview.json).
- The runtime payload used by canonical Rust tests is [`canonical_runtime_preview.json`](../reports/canonical_runtime_preview.json).
- [`fallback_runtime_preview.json`](../reports/fallback_runtime_preview.json) is kept for the compatibility/fallback path only.
- The Rust resolver prefers `canonical_program` when it exists, so forced-canonical tests execute the canonical path directly.
- Canonical execution is therefore real and active in Rust, not just a docs concept.

## Current Numbers

- Draft entries: 1,378
- Canonical-selected in hybrid preview: 1,378
- Legacy fallback in hybrid preview: 0
- Validation failures: 0
- Runtime payload canonical entries: 1,378
- Runtime payload legacy entries: 0
- Runtime payload canonical-only entries: 1,363
- Runtime payload total cards processed: 1,787
- Runtime payload total abilities: 1,363

## Consolidated View

The authored source is now family-centric, and the repeated abilities are grouped in:

- [`canonical_families.json`](../canonical_families.json)
- [`canonical_family_groups.md`](../reports/canonical_family_groups.md)
- [`canonical_family_groups.json`](../reports/canonical_family_groups.json)

That consolidated view reduces the source to 610 exact pseudocode families, including 354 multi-card families.

## What The Engine Actually Consumes

When a canonical ability reaches the engine, the meaningful runtime fields are:

- `canonical_program`
- `source`
- `needs_fallback`
- `fallback_bytecode`

If `canonical_program` is present, canonical resolution is attempted first. If canonical resolution cannot handle an operation, the runtime can fall back to bytecode.

## How The Current Pipeline Works

1. Author or edit the canonical entry in `canonical_families.json`.
2. Regenerate `canonical_full_draft.json` from `canonical_families.json`.
3. Validate structure with `tools/test_normalized_canonical_draft.js`.
4. Validate semantic rules with `tools/canonical_semantic_validator.js`.
5. Lower into the hybrid selection report with `tools/build_hybrid_runtime_preview.js`.
6. Export the canonical-only runtime payload with `tools/build_fallback_runtime.js --canonical-only`.
7. Export the fallback/runtime-compatibility payload with `tools/build_fallback_runtime.js`.
8. Run Rust canonical tests against the canonical-only payload.

## How To Inspect What We Are Feeding The Engine

Use these tools when you want to see the engine-facing shape:

- [`tools/compare_canonical_to_compiled.js`](../../tools/compare_canonical_to_compiled.js)
- [`tools/build_hybrid_runtime_preview.js`](../../tools/build_hybrid_runtime_preview.js)
- [`tools/build_fallback_runtime.js`](../../tools/build_fallback_runtime.js)
- [`engine_rust_src/tests/canonical_semantics.rs`](../../engine_rust_src/tests/canonical_semantics.rs)
- [`engine_rust_src/tests/phase1_fallback_handler.rs`](../../engine_rust_src/tests/phase1_fallback_handler.rs)
- [`engine_rust_src/src/core/logic/canonical.rs`](../../engine_rust_src/src/core/logic/canonical.rs)

## How We Keep Fixing Canonical Entries

1. Fix the family entry in `canonical_families.json`.
2. Regenerate the family report and draft from that source.
3. Rebuild the hybrid preview and confirm the family lands in canonical-selected rather than fallback.
4. Rebuild the canonical-only runtime payload and check that the Rust-loadable JSON reflects the intended canonical family with no fallback bytecode.
5. For any entry that still lowers incorrectly, update the canonical operation mapping in Rust.
6. Add or tighten a Rust test that proves the fix on the exact card or operation family.
7. Re-run the forced-canonical path to confirm the engine sees the corrected payload.

## Recommended Test Loop

```bash
node canonical_ability_model/scripts/build_canonical_family_reports.js
node canonical_ability_model/scripts/build_canonical_full_draft.js
node tools/test_normalized_canonical_draft.js canonical_ability_model/drafts/canonical_full_draft.json
node tools/canonical_semantic_validator.js canonical_ability_model/drafts/canonical_full_draft.json
node tools/build_hybrid_runtime_preview.js canonical_ability_model/drafts/canonical_full_draft.json
node tools/build_fallback_runtime.js --canonical-only
node tools/build_fallback_runtime.js
cargo test --test canonical_semantics -- --nocapture
```

## What Still Needs Work

- The bridge parity gap is still large: many canonical entries differ from the compiled reference even though they now validate.
- More canonical operation families need direct Rust coverage.
- Each new canonical op should get a regression test so forced-canonical mode stays trustworthy.

## Short Version

The current state is: canonical execution is live in Rust, the forced-canonical path is real, but the canonical pipeline still needs cleanup in validation, runtime export, and tests before we can call it complete.
