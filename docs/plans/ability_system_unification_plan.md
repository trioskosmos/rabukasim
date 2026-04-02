# Ability System Unification Plan

## Purpose

This plan describes how to reorganize the ability code so the project keeps the current working functions, but stops routing ability data through a brittle maze of rehydration, packed legacy fields, and late-stage bytecode leftovers.

The goal is not a rewrite for its own sake. The goal is to make ability authoring, loading, execution, suspension, and testing all follow one understandable path:

1. Author the ability once.
2. Normalize it once.
3. Execute it directly.
4. Keep legacy bytecode only in compatibility adapters.

## Problem Statement

The current system works, but it is split across too many representations:

- authored frame data in `data/ability_frame_index.yaml`
- derived consolidated runtime data in `data/consolidated_abilities.json`
- compiled card runtime data in `data/cards_compiled.json`
- typed Rust runtime models in `engine_rust_src/src/core/logic/models.rs`
- interpreter-specific decoding and suspension logic in `engine_rust_src/src/core/logic/interpreter/`
- legacy bytecode helpers, bytecode-shaped tests, and packed-field terminology that still leak into the active path

That split creates the exact pain points that are being felt today:

- frame rehydration is talked about in too many places
- the load path mutates ability data more than it should
- editing frames is hard because the boundaries between source, derived data, and runtime state are blurred
- the end of the pipeline still carries bytecode remnants like packed filter bits and "if filter is 0xff" style logic

## Target State

The target state is a three-layer model with a narrow legacy bridge:

### 1. Authored source layer

This is where humans edit abilities.

Primary inputs:

- `data/cards.json`
- `data/ability_frame_index.yaml`

Responsibilities:

- store the intended ability behavior in a human-editable form
- keep card text, signature, ability index, and frame source tied together
- make frame edits round-trip cleanly without forcing bytecode reasoning

### 2. Normalization layer

This is where authored data becomes runtime-ready, but still structured.

Primary outputs:

- `data/consolidated_abilities.json`
- `data/cards_compiled.json`

Responsibilities:

- merge authored frame data with the rest of the card database
- resolve sparse authored entries into a stable runtime shape
- preserve metadata needed for execution and diagnostics without flattening everything into packed integers

### 3. Runtime execution layer

This is the interpreter and its helpers.

Primary code:

- `engine_rust_src/src/core/logic/models.rs`
- `engine_rust_src/src/core/logic/interpreter/mod.rs`
- `engine_rust_src/src/core/logic/interpreter/instruction.rs`
- `engine_rust_src/src/core/logic/interpreter/suspension.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/unified.rs`

Responsibilities:

- execute typed frames directly
- suspend and resume without reconstructing the ability model from scratch
- keep filter, slot, choice, and target semantics explicit instead of hiding them in packed bytecode-era fields

### 4. Legacy compatibility layer

This layer exists only so old inputs and old tests keep working while the rest of the stack moves forward.

Responsibilities:

- decode old words into typed frames at the boundary
- encode typed frames back to words only when a compatibility path needs it
- keep bytecode-specific logic out of normal authoring and runtime code

## Design Rules

These rules are the core of the plan.

### One canonical runtime shape

All runtime execution should consume the same typed ability structure.

The current Rust `AbilityFrame`, `FrameProgram`, and `Ability` types should stay, but their role should be tightened:

- `AbilityFrame` becomes the primary execution unit
- `FrameProgram` becomes the canonical container for a sequence of frames
- the deprecated `bytecode` field remains for compatibility only

### One loader path

Card loading should produce a single normalized ability representation and not a chain of partial rehydrations.

That means the runtime should not:

- build one shape for storage
- convert it into a second shape for execution
- then rehydrate a third shape during suspension or choice handling

### One place for legacy decoding

All bytecode decoding and packed-field translation should live behind a small compatibility boundary.

That boundary should absorb:

- `FrameProgram::from_words()`
- `FrameProgram::to_words()`
- any other raw-word import/export helper

Normal execution code should not need to know whether the ability came from legacy words or authored frames.

### No runtime repacking in handlers

The interpreter should see typed data, not raw bit layouts.

Handlers should work with:

- decoded filter semantics
- decoded slot semantics
- decoded choice semantics
- decoded look-and-choose counts

They should not be responsible for re-decoding bytecode-era packing just to answer a routine game rule question.

## Proposed Reorganization

### A. Separate source, derived data, and runtime state

The current system already has the right ingredients, but the boundaries are too soft.

The plan is to enforce these roles:

- source: authored YAML and card text
- derived: consolidated JSON and compiled card runtime data
- runtime: typed Rust structures and interpreter state

What this means in practice:

- editing should happen in the authored source, not in derived runtime artifacts
- derived artifacts should be regenerated, not hand-edited
- runtime code should assume it is receiving normalized input

### B. Make ability loading explicit

The card database loader should be responsible for normalization, not for clever transformation.

The current loading logic in `engine_rust_src/src/core/logic/card_db.rs` should be reorganized so it does three explicit things:

1. Load raw card and ability data.
2. Attach the authored frame program if present.
3. Produce a stable runtime `Ability` structure with no extra hidden reconstruction.

Anything that smells like "rehydrate this because another layer forgot to preserve it" should be pulled into the loader boundary or deleted.

### C. Simplify frame interpretation

The interpreter should become the place where frame semantics are executed, not the place where data is repaired.

Specific goals:

- keep `engine_rust_src/src/core/logic/interpreter/mod.rs` as the top-level execution coordinator
- keep `engine_rust_src/src/core/logic/interpreter/handlers/unified.rs` as the handler table
- keep `engine_rust_src/src/core/logic/interpreter/suspension.rs` as the suspension/resume boundary
- remove the need for handlers to understand raw bytecode packing

### D. Quarantine bytecode remnants

The old 5-word shape and packed-bit terminology should survive only where compatibility is unavoidable.

The plan is to move the following into legacy-only territory:

- `BytecodeBuilder` in `engine_rust_src/src/test_helpers.rs`
- `bytecode` on `Ability`
- `to_words()` / `from_words()` as active execution helpers
- packed filter/slot/value reasoning in normal handler code
- semantic comments and logs that still talk about the runtime as if bytecode were the primary model

## Migration Phases

### Phase 0: Inventory and terminology cleanup

Goal: establish a precise map of what is source, what is derived, and what is legacy.

Deliverables:

- audit all ability-related docs, helpers, and runtime modules
- rename any misleading comments that still imply bytecode-first execution
- distinguish frame hydration from legacy decoding

Exit criteria:

- there is a single documented source-of-truth path
- the runtime path is described without using bytecode as the default term

### Phase 1: Normalize the data model

Goal: make ability loading produce one obvious runtime shape.

Deliverables:

- consolidate the ability load path around `FrameProgram` and typed `AbilityFrame` data
- ensure `CardDatabase` attaches loaded frame programs without ad hoc patching
- make the loader preserve all runtime-relevant fields the first time

Exit criteria:

- a loaded ability does not need a second pass to become executable
- ability metadata is present where execution needs it, not reconstructed later

### Phase 2: Decouple execution from packed fields

Goal: make the interpreter consume semantic fields directly.

Deliverables:

- keep filter decoding inside the model boundary
- keep slot decoding inside the model boundary
- keep choice and look-and-choose decoding inside the model boundary
- remove packed-field branching from handler logic where equivalent typed access already exists

Exit criteria:

- handler code reads typed frame fields instead of unpacking integers
- special cases such as look-and-choose, optional costs, and target resolution use explicit helpers

### Phase 3: Clean up suspension and re-entry

Goal: make suspend/resume a control-flow problem, not a data-repair problem.

Deliverables:

- ensure `suspension.rs` preserves execution context without rebuilding the ability representation
- keep the choice stack and execution stack separate from the frame source model
- remove resume-time logic that patches missing data from legacy assumptions

Exit criteria:

- resuming an interaction does not require rehydrating the whole frame program
- execution state and authored ability state are clearly distinct

### Phase 4: Hide legacy bytecode behind adapters

Goal: keep compatibility without letting it define the architecture.

Deliverables:

- keep raw-word import/export helpers only where legacy tests or old data need them
- move any remaining bytecode-shaped parsing into narrow adapter code
- stop using bytecode terminology in normal runtime code paths

Exit criteria:

- new execution code does not need to know about 5-word instructions
- bytecode-only paths are obviously legacy by location and naming

### Phase 5: Remove the leftover packed-field assumptions

Goal: delete the things that only exist because the old model needed them.

Deliverables:

- remove the last runtime dependencies on packed opcode-era conventions
- retire stale helper code in tests and diagnostics where typed frame helpers exist
- update docs and comments so they describe the actual runtime model

Exit criteria:

- the runtime no longer talks about filters and slots as if they were hidden bitfields
- the only remaining bytecode references are in compatibility or regression code

## File-Level Responsibilities

### Source and build tooling

- `data/ability_frame_index.yaml`: authored ability source
- `tools/build_cards.py`: canonical build entrypoint for compiled card data
- `tools/abilities/pipeline.py`: internal pipeline logic that should stay focused on frame-first processing
- `tools/sync_metadata.py`: should not be the place where runtime semantics are rebuilt from layout bits

### Runtime model

- `engine_rust_src/src/core/logic/models.rs`: ability, frame, and program data model
- `engine_rust_src/src/core/logic/interpreter/instruction.rs`: typed decoding of slots and other structured frame fields

### Runtime execution

- `engine_rust_src/src/core/logic/interpreter/mod.rs`: top-level execution flow
- `engine_rust_src/src/core/logic/interpreter/handlers/unified.rs`: handler dispatch for semantic frames
- `engine_rust_src/src/core/logic/interpreter/suspension.rs`: suspend and resume boundaries

### Load and test surfaces

- `engine_rust_src/src/core/logic/card_db.rs`: ability loading and consolidation into the runtime database
- `engine_rust_src/src/test_helpers.rs`: test-only compatibility helpers that should become legacy-only
- `engine_rust_src/src/coverage_gap_tests.rs`: frame-versus-bytecode parity tests that can be simplified as the compatibility layer shrinks
- `engine_rust_src/src/semantic_assertions.rs`: legacy bytecode diagnostics that should be retired or narrowed over time

## What Should Stay

This plan is not trying to throw away everything that already works.

These parts are useful and should be preserved:

- `FrameProgram` as the primary container for ability execution
- `AbilityFrame` as the typed execution atom
- the unified interpreter and handler dispatch model
- suspension and choice handling as first-class runtime behavior
- compatibility decoding for old data and regression tests

## What Should Go Away

These are the patterns that should disappear from normal ability code:

- rehydration as a routine runtime concept
- packed-field reasoning in handlers
- bytecode-first terminology in new code
- hidden repair logic that silently fills missing ability state
- special-case comments that describe execution as a 5-word instruction stream

## Definition Of Done

The work is done when all of these are true:

- authored abilities are edited in the source layer, not in derived runtime artifacts
- runtime execution receives one normalized ability model
- frame execution no longer depends on scattered repacking or rehydration
- bytecode lives only in compatibility adapters and targeted regression tests
- the interpreter and suspension code read like execution code, not repair code
- the docs describe the frame-first model consistently across source, load, and runtime layers

## Practical Order Of Attack

If this is tackled incrementally, the safest order is:

1. clean up terminology and docs
2. lock down the loader boundary
3. simplify the runtime model where the frame data enters Rust
4. remove repacking from handlers
5. narrow the bytecode compatibility path
6. delete the stale helpers and comments that become unreachable

That sequence keeps the current behavior intact while reducing the number of places where ability logic can become inconsistent.