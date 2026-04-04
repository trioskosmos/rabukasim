# Ability Pipeline Code Audit

This document replaces the earlier broad ability-system plan docs. It is derived from the live code path in this workspace.

## Active pipeline

### Authored inputs

The live authored sources are:

- `data/cards.json`
- `data/ability_frame_index.json`
- `data/metadata.json`

`cards.json` holds card identity, stats, and printed text. `ability_frame_index.json` holds authored frame programs keyed by card and ability index. `metadata.json` is the shared schema for symbolic ids and packed layouts.

### Build entrypoint

The public build path is:

- `tools/build_cards.py`
- `tools/abilities/pipeline.py`

`prepare_runtime()` currently:

1. compiles cards
2. validates and normalizes `data/ability_frame_index.json`
3. skips Rust codegen
4. optionally mirrors runtime assets

There is no second active ability-source build artifact. The only active authored ability index is `data/ability_frame_index.json`.

### Python compilation

The live Python compiler path is:

- `engine/compiler/main.py`
- `engine/compiler/semantic_processor.py`

`compile_cards(...)` loads `cards.json`, resolves sparse ability entries, builds `Ability` model objects, populates semantic `effects` / `conditions` / `costs` from authored frames, and writes `data/cards_compiled.json`.

Important current behavior:

- runtime export excludes `frame_program`
- runtime export keeps semantic effects, conditions, and costs
- output is only rewritten when serialized JSON changes

So the compiler is not producing one canonical runtime ability object. It is producing a semantic-only export and relying on Rust to reattach executable frames later.

### Rust load path

The Rust loader path is centered on:

- `engine_rust_src/src/core/logic/card_db.rs`
- `engine_rust_src/src/core/logic/models.rs`

`CardDatabase` loads compiled cards, separately loads the sparse frame index, then mutates loaded abilities to reattach `frame_program`, recover raw text and pseudocode, patch missing `choose_count`, copy runtime fields back into semantic effects, derive top-level conditions from leading condition frames, and compute masks and flags.

This is the biggest structural smell in the current pipeline. Rust is not just loading one runtime model. It is reconstructing one by merging a semantic export with the authored sparse source.

### Trigger and execution path

The active execution path is:

- trigger selection in `game_trigger.rs` and related precheck code
- frame execution in `engine_rust_src/src/core/logic/interpreter/mod.rs`
- handler dispatch under `engine_rust_src/src/core/logic/interpreter/handlers/`
- response generation in `engine_rust_src/src/core/logic/action_gen/response.rs`

The interpreter is frame-first at execution time. The runtime API still exposes `resolve_frames`, `resolve_instructions`, `resolve_words`, and `resolve_bytecode`, but they all funnel into the same frame interpreter after converting words into `FrameProgram`.

### Metadata and generated code

`data/metadata.json` currently serves three live purposes:

1. symbolic registry for opcodes, triggers, conditions, costs, choices, zones, targets, and related ids
2. source of truth for packed attr/value/slot layout definitions
3. source for generated Rust constants and layout files

`tools/sync_metadata.py` reads `metadata.json` and emits `generated_constants.rs` and `generated_layout.rs` plus related generated outputs. So `metadata.json` is not passive metadata. It is the schema that keeps Python packing, Rust unpacking, and generated constants aligned.

## Representation map

The live code still carries too many ability representations.

### A. Authored frames

Location:

- `data/ability_frame_index.json`

Purpose:

- human-edited control flow and effect structure

### B. Python semantic export

Location:

- `data/cards_compiled.json`

Purpose:

- compact runtime export with semantic effects, conditions, and costs

Problem:

- executable frames are stripped, so this cannot stand alone as the one runtime input

### C. Rust runtime frames

Location:

- `AbilityFrame`
- `FrameProgram`
- `Ability` in `engine_rust_src/src/core/logic/models.rs`

Purpose:

- actual execution model

Problem:

- runtime frames are rebuilt by stitching authored data back onto semantic exports

### D. Legacy word form

Location:

- `FrameProgram::from_words()` / `to_words()`
- `BytecodeInstruction`
- `resolve_bytecode*` aliases
- many tests and helpers

Purpose:

- compatibility and old tests

Problem:

- it still shapes API names, test fixtures, and some runtime branches even though execution itself is frame-first

## Main oddities and debt

### 1. The runtime has two ability sources

`cards_compiled.json` and `ability_frame_index.json` are both active runtime inputs. The loader has to merge them back together.

### 2. `card_db.rs` is doing too much repair work

The loader is not just deserializing. It performs lookup aliases, trigger matching, raw text backfill, pseudocode backfill, frame reattachment, semantic backfill, look-and-choose patching, condition derivation, and metadata enrichment.

### 3. Semantic export and frame execution are separate worlds

Python flattens authored frames into semantic effects and conditions, but Rust still executes frames. Trigger prechecks and UI-facing summaries depend on one representation while actual behavior depends on another.

### 4. Raw packed attrs still leak everywhere

The main debt is the dual filter model:

- structured `CardFilter`
- raw `attr` plus passthrough bits

`filter.rs` already splits structured bits from passthrough bits, but runtime code still repeatedly merges and re-splits raw attrs. Helpers in `models.rs` still carry special cases for old encodings, legacy group hints, success-pile sentinels, total-cost flags, and keyword bits.

### 5. Prompt generation still compensates for older shapes

`action_gen/response.rs` still contains compatibility branches such as `legacy_select_mode_option_frames(...)` and `uses_legacy_look_deck_prompt`.

### 6. Runtime APIs still present bytecode as primary terminology

`state.rs` still exposes `resolve_bytecode*` aliases over the same frame interpreter.

### 7. `FrameProgram` still treats bytecode as a first-class compatibility payload

`FrameProgram::from_words()` stores parsed frames plus raw JSON containing `bytecode`, and `to_words()` can prefer preserved raw words over regenerating from frames.

### 8. Python semantic compilation duplicates opcode knowledge

`engine/compiler/semantic_processor.py` hard-codes large opcode-to-effect and opcode-to-condition mappings that overlap with runtime knowledge in Rust.

### 9. `metadata.json` still names the packed schema `bytecode_layout`

That name is stale. The layout is now the canonical schema for packed attr/value/slot fields used by frame execution, not a sidecar for an older bytecode runtime.

## Metadata purpose today

`data/metadata.json` is the registry and schema for the packed pieces that still exist inside frames.

It currently defines:

- opcode ids
- trigger ids
- condition and cost ids
- choice and zone ids
- action bases and extra constants
- packed field layouts for attr, value, and slot words

The important consequence is that the project still has real bitpacking even though it no longer has a bytecode-first runtime. Frame execution is primary, but frame fields still carry packed words.

## Rewrite priorities

### Priority 1: make one runtime ability artifact

Best target state:

- `cards_compiled.json` already contains canonical executable frames
- Rust loads one file and stops reopening `ability_frame_index.json`

That removes the semantic-export-plus-reattachment design.

### Priority 2: split loader repair from data loading

If the one-artifact change is not done first, then `card_db.rs` should still be split into:

- pure file loading
- sparse/frame attachment
- semantic/frame reconciliation
- mask enrichment

Right now those concerns are collapsed into one file.

### Priority 3: replace raw attr juggling with explicit typed fields

The runtime should treat passthrough bits as named compatibility flags, not as opaque leftovers that are repeatedly ORed onto structured filters.

### Priority 4: remove bytecode-named public APIs from live runtime code

The frame interpreter can keep word import helpers internally, but public runtime entrypoints should stop presenting `bytecode` as the default model.

### Priority 5: shrink response-generation compatibility logic

The `legacy_*` prompt helpers in `action_gen/response.rs` should disappear once abilities arrive in one normalized runtime shape.

### Priority 6: reduce duplicated semantic mapping tables

The Python semantic processor and Rust runtime should not both be independently encoding large opcode meaning tables unless there is a clear generated source behind them.

## Simplification ideas for writability

### 1. Author frames with explicit semantic subobjects only

Authored frames should prefer named `semantic.filter`, `semantic.slot`, and `semantic.params` fields. The authored source should not rely on packed attr numbers.

### 2. Rename the packed layout concept

Rename `bytecode_layout` in `metadata.json` to something like `packed_frame_layout`, keeping backward compatibility only in `tools/sync_metadata.py` during migration.

### 3. Make frame export lossless

If the compiler exports frames, it should export the exact runtime frame shape the interpreter uses, not a weaker semantic shadow that Rust must repair.

### 4. Separate filter semantics from compatibility flags

Model selection filters and extra runtime flags as separate fields instead of one overloaded `raw_attr` number.

### 5. Replace word-based test builders with frame builders

Tests should construct `AbilityFrame` and `FrameProgram` directly. Word-based fixtures should become compatibility-only tests.

## Concrete deletion candidates

These are the clearest candidates from the current audit.

### Delete now

- `docs/plans/ability_system_unification_plan.md`
- `docs/plans/ability_system_general_guide_and_deletion_map.md`

### Delete after callers migrate

- `compiler/ability_compiler.py`
- `GameState::resolve_bytecode*` aliases in `state.rs`
- deprecated `BytecodeInstruction`
- `BytecodeBuilder` in test helpers

### Delete after runtime normalization work lands

- `legacy_select_mode_option_frames(...)` in `action_gen/response.rs`
- `uses_legacy_look_deck_prompt` branch in `action_gen/response.rs`
- `FrameProgram::to_words()` as a general runtime helper, keeping only boundary-only compatibility use if still needed

## Concrete rewrite targets

The files with the highest rewrite pressure are:

- `engine_rust_src/src/core/logic/card_db.rs`
- `engine_rust_src/src/core/logic/models.rs`
- `engine_rust_src/src/core/logic/filter.rs`
- `engine_rust_src/src/core/logic/action_gen/response.rs`
- `engine/compiler/main.py`
- `engine/compiler/semantic_processor.py`
- `tools/sync_metadata.py`
- `data/metadata.json`

The root issue is not that the interpreter still executes words. It does not. The root issue is that the system still serializes, exports, rehydrates, and tests abilities as if words and packed attrs were the default conceptual model.