# Rust Frame Migration Plan

## Goal

Make the Rust engine execute abilities from `frame_program` / `sparse_frame_index` only, with bytecode kept strictly as legacy compatibility data.

## Current Direction

- Runtime should resolve abilities from frame data.
- Test fixtures should build frame data directly.
- Bytecode decoding should remain only for compatibility codecs and legacy import/export.

## Step By Step

1. Audit all bytecode touchpoints.
- Find every call to `resolve_bytecode*`.
- Find every use of `FrameProgram::from_bytecode`.
- Find every direct `ability.bytecode` comparison.
- Find every test fixture that constructs `bytecode: vec![...]`.

2. Make runtime frame-first everywhere.
- Keep `resolve_ability()` using `frame_program` first.
- Keep `sparse_frame_index` as the generated fallback.
- Remove any normal execution fallback that decodes bytecode.
- If an ability has no frame data, fail fast instead of silently decoding bytecode.

3. Make loaded card data frame-backed.
- Ensure `CardDatabase` attaches `frame_program` when loading the real database.
- Expand `sparse_frame_index` into `frame_program` during load.
- Do not depend on bytecode to reconstruct runtime abilities.

4. Remove bytecode fallback from model helpers.
- `Ability::semantic_frame_program()` should only return real frame data.
- `Ability::get_frame()` should only read from `frame_program` or `sparse_frame_index`.
- Bytecode should not be used to derive runtime frames in these helpers.

5. Convert test helpers to frames.
- Update synthetic card builders in `test_helpers.rs`.
- Populate `frame_program` directly for helper-created abilities.
- Only keep bytecode in helpers when a test is explicitly about legacy encoding.

6. Rewrite fixture tests to step-by-step frames.
- Replace raw bytecode arrays with explicit `AbilityFrame` sequences.
- For simple cases, use `AbilityFrame::Raw` plus `AbilityFrame::Return`.
- For longer cases, write the exact action order as frames.

7. Keep bytecode only for codec tests.
- Codec tests can still verify round-trips.
- Gameplay tests should not assert on raw bytecode.
- If a test is not about the codec, it should speak frames.

8. Remove legacy resolver wrappers.
- Deprecate `resolve_bytecode`, `resolve_bytecode_cref`, `resolve_bytecode_slice`, and `resolve_bytecode_owned`.
- Delete them once no tests or callers need them.
- Leave only narrow compatibility entry points if external callers still require them.

9. Fix real logic failures exposed by the migration.
- Repair phase suspension behavior.
- Repair optional interaction flows.
- Repair heart, blade, and score propagation bugs.
- Repair nested trigger ordering bugs.

10. Run the full Rust suite after each batch.
- Use `cargo test -- --nocapture`.
- Do not rely on filtered runs as the main proof.
- Keep iterating until the suite is green.

11. Clean up compatibility code.
- Remove stale bytecode fallback branches.
- Remove any test-only adapters no longer needed.
- Keep the codebase frame-native.

12. Final state.
- Frames are the source of truth.
- Sparse frame index is the generated cache.
- Bytecode is legacy only.
- Rust tests are authored against the actual execution model.

## Suggested Work Order

1. Remove remaining bytecode fallback in runtime/model helpers.
2. Convert test helpers to frame programs.
3. Rewrite the failing fixture tests to explicit frames.
4. Re-run the full Rust suite.
5. Fix the real rule bugs the suite exposes.
6. Remove the legacy resolver wrappers.
7. Re-run the full suite until clean.

