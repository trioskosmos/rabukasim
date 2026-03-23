# Radical Ability Runtime / Compiler Split Plan

## Goal

Split the ability system into two clear layers:

- runtime data models in `engine/models/ability.py`
- compilation and parser-facing logic in `compiler/ability_compiler.py`

The end state should make `engine/models/ability.py` a small, stable model module and move all packing, resolving, and bytecode assembly logic into compiler-owned code.

## Why This Refactor Matters

`engine/models/ability.py` is currently doing too much:

- defining runtime-facing data structures
- carrying parser-only helper classes
- compiling instructions into bytecode
- packing runtime metadata
- resolving conditions, costs, and effect metadata

That coupling makes the file hard to reason about, hard to test, and risky to change. The compiler logic should live with the parser and codec pipeline, while runtime models should stay lightweight and serializable.

## Target Shape

### `engine/models/ability.py`

Keep this file focused on runtime models and small convenience methods only.

Keep:

- `Ability`
- `AbilityFrame`
- `FrameProgram`
- minimal dataclass helpers and serialization-friendly methods

Remove:

- `_pack_*` helpers
- `_compile_*` helpers
- `_resolve_*` helpers
- instruction hydration logic
- frame assembly logic
- bitfield manipulation

### `compiler/ability_compiler.py`

Create a compiler-owned module that contains:

- `compile_to_frames(ability_obj)` as the main entry point
- the parser-facing instruction dataclasses:
  - `Effect`
  - `Condition`
  - `Cost`
- all conversion logic from high-level parsed objects to structured `AbilityFrame` dictionaries
- any temporary or intermediate compiler-only helpers needed to preserve current behavior

### `compiler/parser_v2.py`

Update parser imports so it builds the richer instruction objects expected by the new compiler module.

Parser responsibilities should remain:

- parse text into structured instruction objects
- populate the compiler-friendly fields
- avoid bytecode packing or runtime emission work

## Actionable Migration Steps

### Phase 1: Inventory and Freeze Behavior

1. Record the current public surface of `engine/models/ability.py`.
2. Identify every caller that imports `Ability`, `Effect`, `Condition`, or `Cost`.
3. Identify every caller that depends on `Ability.compile()` or frame-generation helpers.
4. Add or confirm parity tests before moving code.

Exit criteria:

- the current API surface is known
- the compile output for representative cards is captured
- no behavior changes have been introduced yet

### Phase 2: Introduce the Compiler Module

1. Add `compiler/ability_compiler.py`.
2. Move `Effect`, `Condition`, and `Cost` definitions into that module if they are only parser/compiler intermediates.
3. Port the frame-construction logic into `compile_to_frames(ability_obj)`.
4. Keep the module self-contained so parser code can import it without pulling in bytecode packing internals.

Exit criteria:

- the compiler module can build the same frame structures as before
- parser code can import the new module successfully
- the compiler module owns all intermediate instruction types

### Phase 3: Shrink `engine/models/ability.py`

1. Remove the packing and resolution helpers from `Ability`.
2. Replace `Ability.compile()` with a thin delegation to the shared codec or compiler utility.
3. Keep only runtime model state and small accessors in the model file.
4. Ensure `Ability`, `AbilityFrame`, and `FrameProgram` remain easy to serialize and inspect.

Exit criteria:

- `ability.py` is short and readable
- the file contains no bit-packing implementation
- runtime models remain compatible with the rest of the engine

### Phase 4: Rewire Parser Imports

1. Update `compiler/parser_v2.py` to import instruction classes from `compiler/ability_compiler.py`.
2. Confirm the parser still produces the richer objects expected by the compiler.
3. Remove any stale references to the old ability-module instruction definitions.

Exit criteria:

- parser import paths are clean
- parser output still compiles
- no circular imports are introduced

### Phase 5: Preserve Bytecode and Frame Parity

1. Run the full card compilation pipeline before and after the split.
2. Compare `bytecode` fields for exact equality.
3. Compare `frame_program` fields for exact equality.
4. Fix any gaps in the compiler shim until parity is restored.

Suggested command sequence:

```powershell
python compiler/main.py data/cards.json data/cards_compiled_before.json
python compiler/main.py data/cards.json data/cards_compiled_after.json
```

Exit criteria:

- `bytecode` matches exactly
- `frame_program` matches exactly
- no regression is introduced in card compilation

## Verification Checklist

### Automated

- `python tools/verify/test_parser_compilation.py`
- `cargo test` in `engine_rust_src`
- database parity comparison for `bytecode` and `frame_program`
- any parser smoke tests that import `AbilityParserV2`

### Manual

- verify `engine/models/ability.py` is under 200 lines
- verify it contains no packing logic
- verify `compiler/ability_compiler.py` contains the compiler-specific instruction types

## Risks

1. Circular imports between `compiler/parser_v2.py`, `compiler/main.py`, and the new compiler module.
2. Behavior drift in optional costs, conditions, or select-mode handling.
3. Hidden callers depending on old instruction definitions in `engine/models/ability.py`.
4. Bytecode parity loss if the compiler shim changes frame ordering or default values.

## Recommended Implementation Order

1. Add the new compiler module without deleting anything.
2. Switch parser imports to the new module.
3. Move `Ability.compile()` to a thin delegation.
4. Delete the old packing and resolution helpers only after parity passes.
5. Trim the runtime module last, once the tests are green.

## Done Means

This refactor is complete when:

- runtime models and compiler logic are separated by module ownership
- `ability.py` is a small runtime model file
- parser code builds compiler-friendly objects from the new module
- the compiled card database is byte-for-byte identical before and after the split
- Rust integration tests still pass

