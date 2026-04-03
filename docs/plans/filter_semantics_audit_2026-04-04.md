# Filter Semantics Audit - 2026-04-04

Goal: separate real gameplay-semantic debt from acceptable packed-layout code.

## Summary

There are still many `0xFF`/`0x7F`/`FILTER_MASK_LOWER` style operations in the repo, but most are not a problem by themselves.

Keep as packed codec/layout code:
- `engine_rust_src/src/core/generated_layout.rs`
- `engine_rust_src/src/core/generated_constants.rs`
- low-level heart/slot/value packing helpers
- AI feature extraction that intentionally reads packed semantic flags

Convert to semantic helpers:
- gameplay logic that infers meaning from raw filter attrs or raw slot bits
- condition handling that masks attrs before matching instead of using `CardFilter` plus passthrough flags
- action generation that extracts zones or target semantics from raw words directly

## Highest-Value Semantic Debt

### 1. `engine_rust_src/src/core/logic/models.rs`

These should become named semantic helpers on `AbilityFrameComponents` instead of ad hoc bit sniffing.

- `semantic_group_id()`
  - still detects legacy low-word group encodings with `0x10`, `0x7F`, and `< 300`
  - should move behind an explicit helper like `legacy_group_id_hint()` or be folded into a broader filter-normalization helper

- `count_filter_attr()`
  - returns `raw_attr & FILTER_MASK_LOWER`
  - this is a compatibility helper, but callers should ideally ask for a semantic count matcher or semantic count payload instead of a raw masked attr

- `heart_compare_color_index()`
  - falls back to `(self.count_filter_attr() & 0x7F) as usize`
  - should be replaced with a semantic color resolver that distinguishes color-mask semantics from legacy low-word color ids

- `resolved_color_index()`
  - still uses `0x7F` and `trailing_zeros()` directly
  - logic is valid, but should be exposed through a named color semantic helper shared with logging and condition code

- `normalized_baton_filter_attr()`
  - still identifies legacy packed baton group forms with `0xFFFFFFFF00000000`, `0x1F`, and `< 300`
  - should become a named legacy-form normalization routine rather than inline bit tests

- `targeted_select_member_filter_attr()`
  - still rewrites target bits via `(filter_attr & !0x3) | TARGET_PLAYER_SELF`
  - should use a semantic filter mutation helper instead of manual low-bit rewriting

- `embedded_count_opcode()`
  - still extracts from `raw_slot >> 8` with a raw flag bit
  - should become a named decoded-slot semantic field if the slot encoding is still part of active gameplay logic

### 2. `engine_rust_src/src/core/logic/action_gen/response.rs`

This file still has repeated raw filter handling that should move behind semantic helpers.

- repeated `filter_attr & !FILTER_STATE_FLAGS_MASK`
  - should use `AbilityFrameComponents::filter_attr_without_state_flags()`-style helpers consistently, or a `PendingInteraction` equivalent

- `packed_zone = (filter_attr >> 12) & 0x0F`
  - direct zone inference from raw attr is semantic debt
  - should become a named helper such as `pending_interaction_target_zone()` or `semantic_selection_zone()`

- direct `CardFilter::from_attr(filter_attr)` mixed with separate raw masked logic
  - indicates the code still treats attrs as partially semantic and partially packed
  - should converge on `CardFilter` plus passthrough helpers

### 3. `engine_rust_src/src/core/logic/interpreter/conditions/opcodes.rs`

- `matcher_attr = attr & FILTER_MASK_LOWER` in `C_COUNT_STAGE`
- `matcher_attr = attr & FILTER_MASK_LOWER` in opcode `306`

These sites should stop pretending the lower word is the whole meaning of the filter. They already use `CardFilter` for structured matching in the same branches. The masking should be replaced by semantic emptiness checks and passthrough-aware helpers.

### 4. `engine_rust_src/src/core/logic/interpreter/conditions/json_params.rs`

- `COUNT_MEMBER` and `ALL_MEMBERS` still derive `matcher_attr = filter_attr & FILTER_MASK_LOWER`

These should align with the shared semantic path used elsewhere:
- merge params through `merge_filter_attr_with_params()`
- use `CardFilter::from_attr(filter_attr)` for structure
- keep passthrough flags like `FILTER_ANY_STAGE` intact at the semantic helper boundary

### 5. `engine_rust_src/src/core/logic/interpreter/handlers/flow_state_mod.rs`

- restriction id via `(a as u64 & FILTER_MASK_LOWER) as u8`
- dynamic count path via `a as u64 & !DYNAMIC_VALUE & FILTER_MASK_LOWER`

These are gameplay-facing and should become named helpers on `AbilityFrameComponents`, for example:
- `restriction_id()`
- `dynamic_count_filter_attr()` or equivalent semantic extractor

### 6. `engine_rust_src/src/core/logic/interpreter/handlers/control_flow.rs`

- negate count uses `(frame_data.resolved_filter_attr() & FILTER_MASK_LOWER).max(1)`

This should be a named semantic field, not a low-word mask in handler code.

## Lower Priority / Mixed Cases

### `engine_rust_src/src/core/logic/interpreter/handlers/movement_discard.rs`

- uses `v & 0x7FFFFFFF` and bit 31 for UNTIL_SIZE behavior

This is still packed-value logic, but it is value-word semantics, not filter semantics. It can be cleaned up later with a named decoder for discard sizing modes.

### `engine_rust_src/src/core/logic/interpreter/logging.rs`

- still has some packed opcode/value decoding like `(a >> 12) & 0x0F` for old move-source descriptions and `(v >> 8) & 0xFF` for look-and-choose counts

These are lower risk than gameplay logic, but they should eventually use named decoded helpers for consistency.

## Probably Fine To Leave Alone

These are not the right targets for the semantics push.

- `engine_rust_src/src/core/generated_layout.rs`
- `engine_rust_src/src/core/generated_constants.rs`
- `engine_rust_src/src/core/hearts.rs`
- `engine_rust_src/src/core/logic/ai_encoding.rs`
- `engine_rust_src/src/core/logic/performance.rs`
- raw bitset fields on player/state structs where the mask is the data model, not an overloaded filter attr

## Recommended Conversion Order

1. Expand `AbilityFrameComponents` semantic helpers in `models.rs`
2. Replace raw attr/zone handling in `action_gen/response.rs`
3. Replace lower-word matcher masking in `conditions/opcodes.rs` and `conditions/json_params.rs`
4. Replace remaining handler-level filter extraction in `flow_state_mod.rs` and `control_flow.rs`
5. Clean up leftover logging/value-word decoders

## Concrete Helper Gaps

Likely missing helpers:

- `resolved_filter_struct_with_passthrough()`
- `has_structured_filter_constraints()`
- `semantic_selection_zone()`
- `legacy_group_id_hint()`
- `resolved_color_semantics()`
- `restriction_id()`
- `dynamic_count_filter_attr()`
- `negate_count_limit()`

The key rule is: gameplay logic should ask semantic questions; only codec/layout boundaries should manipulate raw masks directly.