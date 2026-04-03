# Packed Semantic Audit - 2026-04-03

## Goal

Inventory the remaining Rust runtime code that still recovers semantics from packed words, then group each access by intent so migration can proceed bucket-by-bucket instead of file-by-file.

## Current model

- Edge adapter already exists in `legacy_codec.rs` and parts of `filter.rs`.
- Structured runtime objects already exist: `CardFilter`, `DecodedSlot`, `AbilityFrameComponents`.
- Remaining debt is runtime code that still reads `raw_attr`, `raw_slot`, or legacy bit patterns directly.

## Runtime-priority scan

The focused scan from `scripts/scan_legacy_semantic_functions.py --runtime-priority` found 50 runtime-priority hits.

- `group_resolution`: 14
- `revealed_context`: 13
- `zone_selection`: 8
- `heart_color`: 6
- `success_pile_multiplier`: 6
- `total_cost_budget`: 3

These counts deliberately exclude compatibility-heavy files like `legacy_codec.rs`, `card_db.rs`, `filter_attr_compat.rs`, and interpreter logging.

## Semantic buckets

### 1. Edge adapter / passthrough bits

These are acceptable as compatibility boundaries, but should stay quarantined.

- `engine_rust_src/src/core/logic/legacy_codec.rs`
  - `encode_filter`, `decode_filter`
  - `encode_slot`, `decode_slot`
  - `encode_look_and_choose`, `decode_look_and_choose`
  - `encode_heart_counts`, `decode_heart_counts`
  - `encode_heart_requirements`, `decode_heart_requirements`
- `engine_rust_src/src/core/logic/filter.rs`
  - `CardFilter::to_attr_computed`
  - `CardFilter::from_attr_legacy`
- `engine_rust_src/src/core/logic/models.rs`
  - `AbilityFrame::components`
  - passthrough helpers like `resolved_filter_attr` and `has_revealed_context_passthrough`

### 2. Group resolution

Semantic intent: "which idol group is this frame actually talking about?"

- `engine_rust_src/src/core/logic/filter.rs`
  - `CardFilter::resolve_group_id_from_value`
  - `CardFilter::semantic_group_id`
- `engine_rust_src/src/core/logic/models.rs`
  - `AbilityFrameComponents::semantic_group_id`
- `engine_rust_src/src/core/logic/interpreter/conditions/counts.rs`
  - `resolve_structured_zone_count`
- `engine_rust_src/src/core/logic/interpreter/conditions/opcodes.rs`
  - `resolve_group_id`
  - `legacy_group_id_from_attr`

Status: partly semantic already. Remaining debt is mixed fallback logic in opcode conditions.

Runtime-priority functions:

- `engine_rust_src/src/core/logic/interpreter/conditions/counts.rs`
  - `resolve_structured_zone_count`
- `engine_rust_src/src/core/logic/interpreter/conditions/json_params.rs`
  - `evaluate_raw_condition`
- `engine_rust_src/src/core/logic/interpreter/costs.rs`
  - `resolve_energy_cost`
- `engine_rust_src/src/core/logic/interpreter/handlers/state_member_activate.rs`
  - `handle_activate_member`
- `engine_rust_src/src/core/logic/interpreter/handlers/state_score_bonus.rs`
  - `check_activation_keyword`
- `engine_rust_src/src/core/logic/interpreter/mod.rs`
  - `resolve_semantic_frames`

What needs to be done:

- Separate authored group intent from fallback value-derived group IDs.
- Introduce one resolved group semantic, for example `group_mode = None | Explicit(u8) | FromValue | ActivatedKeyword`.
- Remove opcode-local recovery like `group_id = (attr >> FILTER_GROUP_ID_SHIFT) & 0x7F` from runtime condition handlers.

### 3. Success-pile multiplier / count scaling

Semantic intent: "does this effect scale by success pile count?"

- `engine_rust_src/src/core/logic/rules.rs`
  - `requests_success_pile_multiplier`
  - `frame_uses_count_multiplier`
  - `apply_aura_modifier`

Status: still detected through multiple legacy encodings. This is the clearest remaining example of one semantic recovered from several packed forms.

Runtime-priority functions:

- `engine_rust_src/src/core/logic/rules.rs`
  - `frame_uses_count_multiplier`
  - `requests_success_pile_multiplier`
  - `apply_reduce_cost_modifiers`
  - `apply_aura_modifier`
- `engine_rust_src/src/core/logic/interpreter/handlers/flow_state_mod.rs`
  - `handle_state_modifiers`
- `engine_rust_src/src/core/logic/interpreter/handlers/state_score_bonus.rs`
  - `resolve_dynamic_multiplier`

What needs to be done:

- Promote multiplier source to an explicit semantic, for example `scale = None | SuccessPile | Hand | Discard | Stage | DynamicCount(opcode)`.
- Fold `requests_success_pile_multiplier` into decode-time classification instead of checking four legacy encodings at use sites.
- Update `apply_reduce_cost_modifiers`, `apply_aura_modifier`, and the score/state bonus handlers to consume `scale` rather than raw packed flags.

### 4. Total-cost budget / accumulated-count mode

Semantic intent: "is this selection spending from a shared cost budget rather than consuming a fixed count?"

- `engine_rust_src/src/core/logic/models.rs`
  - `AbilityFrameComponents::uses_total_cost_budget`
  - `PendingInteraction::uses_total_cost_budget`
- `engine_rust_src/src/core/logic/interpreter/handlers/state_member_play_discard.rs`
  - `handle_play_member_from_discard`
- `engine_rust_src/src/core/logic/handlers.rs`
  - discard-play resume branch for `O_PLAY_MEMBER_FROM_DISCARD`

Status: first cleanup landed. Runtime call sites now consume a semantic helper instead of open-coding raw bit checks.

Runtime-priority functions:

- `engine_rust_src/src/core/logic/models.rs`
  - `AbilityFrameComponents::uses_total_cost_budget`
  - `PendingInteraction::uses_total_cost_budget`
- `engine_rust_src/src/core/logic/interpreter/handlers/movement_discard.rs`
  - `handle_move_to_discard`

What needs to be done:

- Finish moving discard/movement flows off `compare_accumulated` as a proxy for budgeted selection mode.
- Replace remaining direct count-mode branching with one semantic such as `count_mode = Fixed | BudgetedCost | DynamicAccumulator`.

### 5. Heart/color decoding

Semantic intent: "which color or heart requirement does this frame refer to?"

- `engine_rust_src/src/core/logic/models.rs`
  - `heart_counts`
  - `heart_requirements_struct`
  - `scalar_dynamic_base`
  - `scalar_dynamic_divisor`
- `engine_rust_src/src/core/logic/rules.rs`
  - `decode_heart_color` closure
  - `decode_heart_requirement_color` closure
- `engine_rust_src/src/core/logic/interpreter/conditions/opcodes.rs`
  - `C_HEART_COMPARE`
- `engine_rust_src/src/core/logic/interpreter/conditions/counts.rs`
  - `resolve_count_components` heart summation branches

Status: partly semantic, but color resolution still mixes params, color masks, and slot fallbacks inline.

Runtime-priority functions:

- `engine_rust_src/src/core/logic/interpreter/conditions/counts.rs`
  - `resolve_count_components`
- `engine_rust_src/src/core/logic/interpreter/handlers/flow_select.rs`
  - `normalize_select_member_filter_attr`
- `engine_rust_src/src/core/logic/interpreter/instruction.rs`
  - `decode`
- `engine_rust_src/src/core/logic/models.rs`
  - `heart_counts`
- `engine_rust_src/src/core/logic/performance.rs`
  - `semantic_heart_color_from_frame`
  - `execute_performance_phase`

What needs to be done:

- Centralize color interpretation into a single semantic field, for example `color_mode = None | ExplicitMask(u8) | SelectedColor | SlotInferred | AnyColor`.
- Make rules and conditions consume the resolved color semantic rather than re-decoding masks and slots inline.

### 6. Zone selection / slot targeting

Semantic intent: "which zone or slot is the effect reading from or writing to?"

- `engine_rust_src/src/core/logic/rules.rs`
  - `is_generic_cost_area_slot`
  - `apply_aura_modifier`
- `engine_rust_src/src/core/logic/interpreter/conditions/counts.rs`
  - `is_structured_zone_count`
  - `resolve_structured_zone_count`
- `engine_rust_src/src/core/logic/interpreter/handlers/flow_select.rs`
  - `resolve_select_member_target_player`
  - `handle_select_ops`
- `engine_rust_src/src/core/logic/interpreter/handlers/interaction_look_choose.rs`
  - `handle_look_and_choose`

Status: several handlers still inspect raw slot encodings or preserve raw slot words for compatibility.

Runtime-priority functions:

- `engine_rust_src/src/core/logic/handlers.rs`
  - `resolve_pending_stage_slot`
- `engine_rust_src/src/core/logic/interpreter/conditions/opcodes.rs`
  - `check_condition_frame`
- `engine_rust_src/src/core/logic/interpreter/handlers/flow_select_resolve.rs`
  - `selected_target_key`
- `engine_rust_src/src/core/logic/interpreter/handlers/state_member_play_discard.rs`
  - `discard_play_slot_is_legal`
- `engine_rust_src/src/core/logic/interpreter/instruction.rs`
  - `decode`
  - `to_raw`
- `engine_rust_src/src/core/logic/rules.rs`
  - `calculate_board_aura`

What needs to be done:

- Separate zone selection semantics from slot encoding details.
- Introduce one slot/zone semantic such as `targeting_mode = ExplicitSlot | AnyStage | BatonOnly | ContextSlot | SourceZoneDerived`.
- Remove runtime dependence on magic slot integers where `DecodedSlot` is already available.

### 7. Keyword flags

Semantic intent: "was an energy/member/group keyword activated?"

- `engine_rust_src/src/core/logic/filter.rs`
  - `keyword_energy`, `keyword_member` decode/encode
- `engine_rust_src/src/core/logic/interpreter/conditions/opcodes.rs`
  - `C_HAS_KEYWORD`

Status: mixed semantic and raw-flag checks. Group keyword handling should migrate to one structured keyword request model.

### 8. Revealed-context passthrough

Semantic intent: "does this condition intentionally read from the revealed/looked-card context?"

- `engine_rust_src/src/core/logic/models.rs`
  - `AbilityFrameComponents::has_revealed_context_passthrough`
- `engine_rust_src/src/core/logic/interpreter/conditions/opcodes.rs`
  - `has_revealed_context_passthrough`
  - `C_HAS_KEYWORD` revealed/looked-card branch
- `engine_rust_src/src/core/logic/filter_attr_compat.rs`
  - passthrough construction for `FILTER_REVEALED_CONTEXT`

Status: still split between passthrough detection and runtime behavior.

Runtime-priority functions:

- `engine_rust_src/src/core/logic/interpreter/conditions/opcodes.rs`
  - `has_revealed_context_passthrough`
  - `check_condition_with_parts`
- `engine_rust_src/src/core/logic/interpreter/handlers/flow_select.rs`
  - `handle_select_ops`
- `engine_rust_src/src/core/logic/interpreter/handlers/state_member_play_discard.rs`
  - `handle_play_member_from_discard`
- `engine_rust_src/src/core/logic/interpreter/handlers/state_member_play_discard_select.rs`
  - `handle_discard_selection`
- `engine_rust_src/src/core/logic/interpreter/handlers/unified.rs`
  - `handle_draw`
- `engine_rust_src/src/core/logic/models.rs`
  - `add_to_hand_uses_looked_cards`
  - `has_revealed_context_passthrough`

What needs to be done:

- Replace passthrough-bit checks with a named semantic context source, for example `context_mode = Default | LookedCards | RevealedCards | BatonSources | SelectedCards`.
- Stop treating `FILTER_REVEALED_CONTEXT` as a runtime behavior primitive outside compatibility decode.

## Proposed semantic frame adapter

The next migration step should be a decode-once adapter layered on top of `AbilityFrameComponents`.

Suggested shape:

```rust
struct SemanticFrameView {
    filter: SemanticFilter,
    slot: SemanticSlot,
    value: SemanticValue,
    scale: SemanticScale,
    group: SemanticGroup,
    count_mode: SemanticCountMode,
    color_mode: SemanticColorMode,
    context_mode: SemanticContextMode,
    targeting_mode: SemanticTargetingMode,
}
```

Suggested responsibilities:

- `SemanticFilter`
  - Normal card filter fields already decoded by `CardFilter`.
  - No raw bit inspection in consumers.
- `SemanticSlot`
  - Structured source zone, destination zone, target slot, dynamic markers.
- `SemanticValue`
  - Fixed scalar, decoded heart counts, decoded heart requirements, or dynamic scalar metadata.
- `SemanticScale`
  - `None | SuccessPile | Hand | Discard | Stage | DynamicCount(opcode)`.
- `SemanticGroup`
  - `None | Explicit(u8) | FromValue | ActivatedEnergyByGroup | ActivatedMemberByGroup`.
- `SemanticCountMode`
  - `Fixed | BudgetedCost | DynamicAccumulator | ZoneCount`.
- `SemanticColorMode`
  - `None | ExplicitMask(u8) | SelectedColor | SlotInferred | AnyColor`.
- `SemanticContextMode`
  - `Default | LookedCards | RevealedCards | SelectedCards | BatonSources`.
- `SemanticTargetingMode`
  - `ExplicitSlot | AnyStage | BatonOnly | ContextSlot | SourceZoneDerived`.

Decode boundary:

- Raw `attr`, `slot`, `value`, and `params` are decoded once when constructing the semantic view.
- Legacy compatibility flags remain legal only in decode/import layers.
- Runtime handlers receive `SemanticFrameView` or helper accessors derived from it.

Runtime payoff:

- `rules.rs` stops recovering scale/color/zone intent inline.
- `conditions/opcodes.rs` stops recomputing group/revealed-context semantics from packed words.
- selection/discard handlers stop using passthrough bits as behavior toggles.

## Conversion order

1. Success-pile multiplier
   - Introduce one semantic field for multiplier source.
   - Remove the multi-encoding checks from `rules.rs` runtime paths.

2. Revealed-context conditions
  - Convert look/reveal passthrough checks into explicit context-source semantics.

3. Group keyword resolution
  - Replace `C_HAS_KEYWORD` and related group checks with a structured group request.

4. Heart/color decoding
   - Centralize color resolution so rules and conditions stop decoding color intent inline.

5. Zone selection
   - Push remaining zone/slot fallback logic behind `DecodedSlot` or a higher-level selection model.

6. Remaining total-cost budget cleanup
  - Finish movement/discard runtime consumers that still treat accumulated compare as behavior.

## Principle for the next passes

- Detect intent once.
- Name the intent in the model layer.
- Let runtime handlers consume the named semantic.
- Leave raw packing only in import/export, fixtures, and compatibility shims.