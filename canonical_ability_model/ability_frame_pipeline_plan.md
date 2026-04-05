# Ability Frame Pipeline Plan

## Goal
Make the ability frame pipeline much simpler while keeping runtime behavior the same.

## Current End-to-End Pipeline
1. `tools/abilities/pipeline.py` loads authored ability data from `data/ability_frame_source.json`.
2. `tools/frame_codec.py` normalizes entries into a canonical flat shape:
   - frame opcodes are normalized
   - signatures are recomputed from opcode sequence
   - card reference labels are rebuilt
   - text coverage and opcode catalog are derived
3. `tools/frame_codec.py` then emits two runtime-facing projections from the same normalized payload:
   - compact source payload
   - runtime payload with `readable` overlays and semantic display text
4. `engine/compiler/main.py` reads the compact sparse index and builds Python `Ability` objects.
5. `engine/compiler/semantic_processor.py` converts those frames into semantic `effects`, `conditions`, and `costs`.
6. `engine/compiler/main.py` exports `data/cards_compiled.json` with `frame_program` and `raw_text` preserved in runtime mode.
7. `engine_rust_src/src/core/logic/card_db.rs` only reloads `data/ability_runtime_index.json` when a compiled ability is missing executable frames or raw text.
8. `engine_rust_src/src/core/logic/ability_hydration.rs` patches runtime fields back onto `Ability` objects only in that fallback path.
9. `engine_rust_src/src/core/logic/models.rs` resolves executable frames from `frame_program` first and only falls back to semantic effects for legacy or underspecified payloads.

## Where Conversion Loops Exist
- Frames are converted to semantic effects in Python, then converted back into executable frames in Rust.
- Review and runtime views are both generated from the same helper path, so review depends on runtime decoration.
- LOOK_AND_CHOOSE choose-count and other runtime details are inferred from text in Python, then rehydrated from frames in Rust.
- Card references still pass through string labels and are parsed back into `card_no#ab_idx` pairs in multiple places.

## Example Ability Path
Example source in `data/ability_frame_source.json`:
- `MOVE_TO_DISCARD`
- `JUMP_IF_FALSE`
- `SUM_VALUE`
- `JUMP_IF_FALSE`
- `LOOK_AND_CHOOSE`
- `RETURN`

What happens today:
1. Source frames are normalized and signed.
2. Review/runtime projections add display metadata.
3. Python semantic processing collapses the frame sequence into conditions and effects.
4. Rust reloads the frame sequence again from the sparse index.
5. The interpreter executes the reloaded frames.

## What Should Be Removed
- The review payload should not be built by first building runtime payload.
- Runtime cards should not have to reload sparse frame programs from the index if they already carry executable frames.
- Semantic lists should be derived output, not the bridge back into execution.
- String parsing of card references should be replaced with structured lookup data.

## Fallback Audit
Removed in this cleanup pass:
- `engine_rust_src/src/core/logic/interpreter/conditions/opcodes.rs`
   - Deleted the `cid == 557` special-case energy-count bypass.
   - Validation: the direct repro and QA tests still pass, so the current compiled/authored data is sufficient.
- `engine_rust_src/src/core/logic/interpreter/handlers/flow_select.rs`
   - Deleted the second-pass `structured_fallback` branch for `SELECT_MEMBER` candidate discovery.
   - Validation: the full Rust suite still passes, so the primary matcher is now sufficient.

Still present and should be removed by fixing source/compiler data rather than adding new runtime exceptions:
- `engine_rust_src/src/core/logic/interpreter/mod.rs`
   - `source_card_id == 4849` activated-ability branch.
   - `source_card_id == 8844` activated-ability branch.
   - These are not acceptable end-state runtime rules. They exist because the compiled/authored activated `frame_program` for those cards is still underspecified relative to the printed card text.

Still present as compatibility layers with a clearer justification:
- `engine_rust_src/src/core/logic/card_db.rs`
   - Sparse runtime-index hydration fallback when compiled cards are missing `frame_program` or `raw_text`.
- `engine_rust_src/src/core/logic/models.rs`
   - Legacy modal/select reconstruction and packed-layout compatibility helpers.
- `engine_rust_src/src/core/logic/handlers.rs`
   - `legacy_activation_prefix_text` helpers used to infer missing activated-cost metadata from printed text when structured cost frames are absent.

These remaining layers should be retired in this order:
1. Repair authored/source frame data for card-specific gaps like `4849` and `8844`.
2. Stop inferring activated costs from printed text once those frames are present in compiled cards.
3. Remove sparse hydration fallback after the runtime card export is complete enough to stand alone.
4. Remove legacy modal/select reconstruction after all modal abilities carry structured option frames.

## Card-ID Audit
The remaining `cid == x` / `source_card_id == x` runtime branches were reviewed explicitly.

Runtime hardcodes that were removed:
- `557` energy gate bypass in condition evaluation.

Runtime hardcodes still present:
- `4849`
   - Printed card text requires: discard 1 card, select a live in discard, pay energy equal to that live's score, then recover it.
   - Current compiled data only exports an optional `RECOVER_LIVE` frame and does not encode the discard-plus-variable-energy sequence.
- `8844`
   - Printed card text requires: pay `EE`, discard 1 hand card, branch on whether the discarded card is `μ's`, then either look at 4 and take 2 or recover a live from discard.
   - Current compiled data exports `DISCARDED_CARDS` gates and branch effects, but does not encode the actual energy payment and hand-discard interaction as executable frames.

Conclusion:
- Remaining `cid == x` logic is no longer being treated as "good enough" compatibility. It is now documented as authored/compiler debt that should be removed by fixing the source frames, not by preserving the runtime branches indefinitely.

## Updated Pipeline
Target shape:
1. One canonical authored frame index.
2. One normalized frame model.
3. One runtime card export that keeps `frame_program`.
4. Semantic `effects`/`conditions`/`costs` as derived compatibility data.
5. No Rust sparse reattachment in the normal runtime load path.

Desired flow:
- `ability_frame_source.json`
- normalize and validate frames once
- export compiled cards with `frame_program` preserved
- derive semantic metadata for compatibility and inspection
- load compiled cards directly in Rust
- execute the preserved `frame_program` directly

## First Implementation Slice
1. Split `tools/frame_codec.py` into a small public facade plus helper modules for normalization and display projection.
2. Keep `tools/frame_codec.py` API-compatible so callers do not change.
3. Stop generating review as a derivative of runtime; make review and runtime direct projections from the normalized payload.
4. Keep the current behavior of signatures, card refs, readable overlays, and metadata preservation.

## Next Refactor Slice
1. Preserve `frame_program` in runtime card exports.
2. Remove the need for Rust to reattach sparse frame programs during normal card loading.
3. Replace string-based card reference reconstruction with structured `card_refs` everywhere feasible.
4. Replace the remaining `4849` and `8844` interpreter hardcodes with proper authored frame programs and then delete the source-card branches.
5. Remove text-inferred activated-cost fallbacks once the authored frames cover those costs directly.

## Example Complex Ability
A representative ability with optional discard plus look-and-choose already exists in the authored data and is suitable for regression coverage.

Files to watch:
- [tools/abilities/pipeline.py](../tools/abilities/pipeline.py)
- [tools/frame_codec.py](../tools/frame_codec.py)
- [engine/compiler/main.py](../engine/compiler/main.py)
- [engine/compiler/semantic_processor.py](../engine/compiler/semantic_processor.py)
- [engine_rust_src/src/core/logic/ability_hydration.rs](../engine_rust_src/src/core/logic/ability_hydration.rs)
- [engine_rust_src/src/core/logic/card_db.rs](../engine_rust_src/src/core/logic/card_db.rs)
- [engine_rust_src/src/core/logic/models.rs](../engine_rust_src/src/core/logic/models.rs)
