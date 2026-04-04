# Ability Source, Hydration, and Runtime Execution

This document describes the live authored-source to runtime path in the current workspace after the hydration extraction into `engine_rust_src/src/core/logic/ability_hydration.rs`.

## Executive summary

The current system has one authored ability source and one compiled semantic export, but the Rust runtime still reconstructs executable frame detail by merging them.

The real flow today is:

1. `data/cards.json` defines card identity and printed text.
2. `data/ability_frame_index.json` defines the authored frame program per card ability.
3. `engine/compiler/main.py` compiles cards into `data/cards_compiled.json`, keeping semantic `effects` / `conditions` / `costs` and intentionally dropping `frame_program` in the runtime export.
4. `engine_rust_src/src/core/logic/card_db.rs` loads `cards_compiled.json`.
5. `engine_rust_src/src/core/logic/ability_hydration.rs` reloads `ability_frame_index.json`, reattaches `frame_program`, backfills missing low-level runtime fields, and repairs a few opcode-specific gaps.
6. `Ability::resolved_frames()` in `engine_rust_src/src/core/logic/models.rs` chooses the executable frame view.
7. `engine_rust_src/src/core/logic/interpreter/mod.rs` executes those frames through handler modules.

That means the source of truth for what an ability is remains the authored frame index, while hydration is the process that fills in engine-facing details the semantic export does not preserve.

## Current source of truth

### Authoring layer

The authored layer is split across three files:

- `data/cards.json`: card stats, names, printed text, sparse card-level authored fields.
- `data/ability_frame_index.json`: authored frame programs keyed by card number and ability index.
- `data/metadata.json`: shared registry for trigger ids, opcode ids, condition ids, cost ids, and packed attr/value/slot layouts.

For ability behavior, `data/ability_frame_index.json` is the decisive authored source.

### Build layer

The public build entrypoint is `tools/build_cards.py`, which calls `tools/abilities/pipeline.py`.

The runtime build does two things that matter here:

1. It compiles `cards.json` into `cards_compiled.json` using `engine/compiler/main.py`.
2. It validates `ability_frame_index.json` through `tools/frame_codec.py` but does not fold that authored frame program into the compiled runtime artifact.

This is intentional in the current code. `engine/compiler/main.py` explicitly describes the runtime export as semantic-only and says Rust will rebuild executable frames from authored sparse data and semantic fallbacks.

## The hydration boundary

The hydration boundary is now explicit in the Rust code:

- Loader: `engine_rust_src/src/core/logic/card_db.rs`
- Hydration module: `engine_rust_src/src/core/logic/ability_hydration.rs`
- Runtime frame resolution: `engine_rust_src/src/core/logic/models.rs`

The loader is responsible for deserializing cards. The hydration module is responsible for turning a compiled semantic ability plus sparse authored frames into a runtime ability that the interpreter can execute.

The key entrypoints are:

- `CardDatabase::from_value(...)`
- `ability_hydration::load_sparse_ability_index_from_json(...)`
- `ability_hydration::attach_sparse_ability_index(...)`
- `Ability::resolved_frames()`

## What hydration means here

Hydration is not one thing. There are three layers.

### 1. Generic frame decoding

This happens in `AbilityFrame::from_json_value(...)` in `engine_rust_src/src/core/logic/models.rs`.

For every authored frame, regardless of opcode, the runtime does all of the following:

- chooses the active payload from `semantic`, direct fields, or single-key legacy forms
- resolves opcode from `opcode_name`, `opcode`, `op`, or keyed shorthand
- resolves `value` from `value`, `count`, `rule_type`, `v`, or nested param payloads
- resolves `params` and `options`
- resolves `is_cost`
- resolves negation flags
- decodes structured filter data via `CardFilter::from_frame_json(...)`
- preserves passthrough filter bits that are not representable in the structured filter
- decodes slot data into `DecodedSlot`
- normalizes zone text like `HAND`, `DISCARD`, `STAGE`, `DECK`, `SUCCESS_PILE`

This is the universal hydration pass. Almost every opcode uses only this layer and no opcode-specific repair in the loader.

### 2. Ability attachment and repair

This happens in `ability_hydration::attach_sparse_ability_index(...)`.

For each compiled ability on a card, Rust:

1. resolves card-number aliases such as `+` versus `＋` and some `PL!-` to `PL!HS-` lookups
2. finds the matching authored sparse entry by card number plus ability index
3. verifies trigger compatibility when multiple sparse entries might exist
4. fills in `raw_text` from `source_text` or `source_text_en` when the compiled export omitted it
5. reattaches `frame_program`
6. fills in missing `pseudocode`
7. backfills missing runtime fields on semantic effects from matching authored frames

The backfilled effect fields are:

- `runtime_opcode`
- `runtime_value`
- `runtime_attr`
- `runtime_slot`
- `params` when the semantic export was missing usable detail
- `is_optional` in a few cases where the frame or printed text implies optionality

### 3. Runtime semantic normalization

This happens after hydration when the interpreter or response generator asks questions of a frame through `AbilityFrameComponents` methods in `engine_rust_src/src/core/logic/models.rs`.

Examples:

- `resolved_filter_attr()` merges structured filter reconstruction with raw passthrough bits.
- `semantic_discard_spec()` turns low-level discard words into prompt-facing discard semantics.
- `semantic_look_and_choose_spec()` turns packed look-and-choose words into explicit counts, zones, remainder behavior, and filter state.
- `targeted_select_member_filter_attr()` strips count-like bits that should not be treated as member filter constraints.
- `add_to_hand_uses_looked_cards()` decides whether `ADD_TO_HAND` should draw from deck or consume the looked-card buffer.

This is important architecturally: many semantics are not decided at load time. They are delayed until execution-time helper methods inspect the hydrated frame.

## Opcode-level hydration map

The crucial architectural fact is that most opcodes do not have unique loader-time hydration. They all go through generic frame decoding, then their meaning is interpreted later by runtime helpers or handlers. Only a small subset gets special repair during attachment.

### Control-flow opcodes

Opcodes:

- `RETURN`
- `JUMP`
- `JUMP_IF_FALSE`

Hydration behavior:

- decoded generically into `AbilityFrame`
- excluded from effect metadata backfill in `frame_matches_effect_metadata(...)`
- never treated as semantic effects
- preserved only to drive interpreter control flow

What happens in-between:

- `JUMP_IF_FALSE` is the bridge between leading condition frames and the next executable block
- `RETURN` terminates the active frame program branch
- these opcodes do not mutate game state themselves; they only decide where execution continues

### Condition opcodes

Representative opcodes:

- `COUNT_STAGE`
- `COUNT_HAND`
- `COUNT_DISCARD`
- `COUNT_ENERGY`
- `COUNT_HEARTS`
- `COUNT_BLADES`
- `COUNT_GROUP`
- `HAS_MEMBER`
- `HAS_KEYWORD`
- `SUM_VALUE`
- other ids in the two condition ranges defined in interpreter constants

Hydration behavior:

- decoded generically from authored frames
- may also have semantic conditions from the compiled export
- when the runtime decides the frame program is authoritative, `derive_conditions_from_frame_program(...)` replaces `ab.conditions` with the leading contiguous authored condition block

Why this exists:

- the compiler can flatten branch-local checks into top-level semantic conditions
- the interpreter needs the leading authored condition block instead, because those checks are the true pre-branch guard

What happens in-between:

- conditions are read during trigger precheck and interpreter evaluation
- some condition prechecks are deliberately deferred if an interactive frame appears before the relevant count condition

### `LOOK_AND_CHOOSE`

This is the strongest example of real opcode-specific hydration.

Loader-time repair:

- if the authored frame lacks `choose_count`, Rust copies it from the semantic effect params
- if necessary Rust also writes `count` and `choose_count` back into frame params

Runtime normalization:

- `AbilityFrame::look_choose()` merges packed value bits with params overrides
- `semantic_look_and_choose_spec()` computes explicit `look_count`, `choose_count`, `source_zone`, `target_slot`, `remainder_zone`, `remainder_to_discard`, and selection filter state

Handler/runtime usage:

- prompt generation and suspension logic use the normalized spec
- the deck handlers decide where the remainder goes after the choice resolves

### `MOVE_TO_DISCARD`

Loader-time repair:

- effect runtime fields are backfilled from the authored frame
- if the runtime slot is still zero but printed text implies hand discard, Rust patches `source_zone = Hand`

Runtime normalization:

- `semantic_discard_spec()` infers discard source zone, optionality, prompt filter, and count handling

What happens in-between:

- the frame does not just mean “discard something”
- hydration supplies the source zone and prompt context so the engine knows whether the discard comes from hand, stage, discard, or a default/fallback zone

### Selection opcodes

Opcodes:

- `SELECT_MEMBER`
- `SELECT_LIVE`
- `SELECT_PLAYER`
- `SELECT_CARDS`
- `SELECT_MODE`
- `COLOR_SELECT`

Loader-time repair:

- effect runtime words and params are backfilled from authored frames when missing
- optionality can be inferred from frame flags or printed text

Runtime normalization:

- `targeted_select_member_filter_attr()` removes count-like packed fields that would otherwise be misread as filter constraints
- `normalized_select_member_filter_attr()` rewrites a common packed ambiguity into a clean member filter
- `resolved_filter_attr()` carries passthrough bits into response generation and validation

Metadata enrichment side effects:

- `choice_flags`
- `choice_count`
- `requires_selection`

These are inferred in `CardDatabase::enrich_member_runtime_metadata(...)` and `CardDatabase::enrich_live_runtime_metadata(...)` by examining hydrated frames.

### Deck-look and deck-order opcodes

Opcodes:

- `LOOK_DECK`
- `LOOK_DECK_DYNAMIC`
- `REVEAL_UNTIL`
- `ORDER_DECK`
- `MOVE_TO_DECK`
- `ADD_TO_HAND`

Loader-time repair:

- mostly generic only

Runtime normalization and legacy support:

- `add_to_hand_uses_looked_cards()` determines whether `ADD_TO_HAND` should consume a reveal/search buffer rather than draw normally
- `movement_deck.rs` still has legacy remainder-resolution helpers for older authored patterns

Architectural implication:

- these opcodes are hydrated lightly at load time but interpreted heavily at handler time

### Cost opcodes

Representative opcodes:

- `PAY_ENERGY`
- `PAY_ENERGY_DYNAMIC`
- `SET_TAPPED`
- `TAP_MEMBER`
- some selection/discard opcodes when marked `is_cost`

Hydration behavior:

- `AbilityFrame::from_json_value(...)` resolves `is_cost` from frame fields, params, or options
- semantic costs exist in parallel in the compiled export
- the interpreter still has compatibility logic for “legacy costs” when optional frame structure is missing

Architectural implication:

- cost semantics are still partly split between semantic export and frame execution

### Meta/rule opcodes

Representative opcodes:

- `META_RULE`
- `RESTRICTION`
- `PREVENT_PLAY_TO_SLOT`
- `PREVENT_SET_TO_SUCCESS_PILE`
- `PREVENT_ACTIVATE`
- `PREVENT_BATON_TOUCH`
- `GRANT_ABILITY`
- `TRIGGER_REMOTE`

Hydration behavior:

- no special loader repair beyond generic frame decoding and runtime field backfill
- semantics come almost entirely from `value`, `resolved_filter_attr()`, slot words, and params read by the handlers

### Score, heart, blade, and state modifiers

Representative opcodes:

- `DRAW`
- `ADD_BLADES`
- `ADD_HEARTS`
- `BOOST_SCORE`
- `SET_SCORE`
- `REDUCE_SCORE`
- `REDUCE_COST`
- `REDUCE_HEART_REQ`
- `INCREASE_COST`
- `INCREASE_HEART_COST`
- `TRANSFORM_COLOR`
- `TRANSFORM_HEART`
- `TRANSFORM_BLADES`
- `ACTIVATE_MEMBER`
- `TAP_MEMBER`
- `SET_TAPPED`

Hydration behavior:

- almost entirely generic
- handlers interpret packed fields through `AbilityFrameComponents`
- some runtime metadata such as modifier caches and opcode masks are derived later during card enrichment

## The semantic fallback path

`Ability::resolved_frames()` in `engine_rust_src/src/core/logic/models.rs` makes the split explicit.

It resolves frames in this order:

1. use `frame_program.frames` if the frame program matches semantic effects
2. otherwise synthesize frames from semantic effects
3. otherwise use the frame program even if it does not align with effects

This is why the runtime can still execute an ability even when the sparse frame source or the semantic export is incomplete, but it is also why the codebase still carries dual representations.

## Runtime file structure assessment

### Files that are clearly needed

These are the core pieces of the current architecture:

- `engine_rust_src/src/core/logic/models.rs`: runtime frame model, helper semantics, resolution rules
- `engine_rust_src/src/core/logic/filter.rs`: structured filter representation and passthrough-bit split
- `engine_rust_src/src/core/logic/ability_hydration.rs`: authored-frame attachment and repair boundary
- `engine_rust_src/src/core/logic/card_db.rs`: card database load, lookup, and enrichment
- `engine_rust_src/src/core/logic/interpreter/mod.rs`: execution loop and orchestration
- `engine_rust_src/src/core/logic/interpreter/handlers/*`: per-family execution behavior
- `engine_rust_src/src/core/logic/action_gen/response.rs`: user-facing prompt/action generation over hydrated frames
- `engine_rust_src/src/core/logic/game_trigger.rs`: trigger precheck and queueing over hydrated frames

### Splits that are justified

The broad interpreter split is justified when it separates real domains:

- movement
- interaction / suspended choice flows
- state mutation
- control flow
- condition evaluation
- cost payment

That split reflects different execution concerns and keeps handler functions shorter.

### Splits that are probably excessive

The current handler tree is probably over-split below the family level. There are too many tiny files in `interpreter/handlers/` that fragment closely related member-play and energy-placement flows. The cost is navigation overhead and weaker local reasoning.

Reasonable next consolidation target:

- keep family modules like `movement`, `interaction`, `state_member`, `state_energy`, `flow_select`
- collapse the tiny per-substep files under each family unless they are reused independently

I did not make that consolidation in this pass because it would be large and behavior-risky compared with the hydration extraction.

### The most important structural smell before this change

Before this change, the authored ability reattachment and repair logic lived inside `card_db.rs`. That made the database module responsible for:

- file loading
- sparse-source parsing
- trigger matching
- text backfill
- pseudocode backfill
- frame-program reattachment
- effect runtime backfill
- opcode-specific repair

That was the wrong boundary. The hydration extraction fixes that first-order problem without changing runtime behavior.

## Fixes made in this pass

### 1. Hydration extracted into a dedicated runtime module

Added:

- `engine_rust_src/src/core/logic/ability_hydration.rs`

This module now owns:

- sparse index JSON loading
- authored frame attachment
- leading condition derivation
- effect runtime backfill
- opcode-specific hydration repair for `LOOK_AND_CHOOSE` and `MOVE_TO_DISCARD`

### 2. `card_db.rs` now delegates hydration instead of embedding it

`card_db.rs` still calls hydration during load, but the responsibility is explicit and centralized.

This is the main architecture fix from this document.

## Recommended target architecture

The correct long-term shape is still:

1. one authored source of behavior: frame-authored abilities
2. one compiled runtime artifact containing lossless executable frames plus semantic summaries
3. one runtime load path that does deserialization and lightweight validation, not reconstruction

In that model, hydration becomes a build-time concern instead of a runtime repair step.

The current code is not there yet. This pass only makes the existing runtime repair boundary explicit and better contained.