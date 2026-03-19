# Ability / Effect / Parser Refactor Plan

## Goal

Untangle the high-complexity Python surfaces around ability parsing, effect execution, and pseudocode parsing while preserving behavior, keeping Japanese text intact, and reducing the risk of encoding regressions.

This plan focuses on:

- `engine/models/ability.py`
- `engine/game/mixins/effect_mixin.py`
- `compiler/parser_v2.py`

It also includes a dedicated encoding cleanup plan so mojibake does not reappear while these files are being split.

## Current Problems

### `engine/models/ability.py`

This file currently mixes several different responsibilities:

- ability schema and runtime-facing data classes
- generated enum and metadata plumbing
- description tables, including Japanese strings
- packed filter helpers
- semantic or compiler-adjacent logic
- bytecode/structured representation helpers

The result is a file that is too easy to break when moving text or helper code, especially when the file contains non-ASCII strings.

### `engine/game/mixins/effect_mixin.py`

This file still acts like a gameplay orchestration hub even though the long-term engine direction is Rust-first.

It currently mixes:

- rule checks
- trigger dispatch
- cost payment
- condition checks
- effect resolution
- choice handling
- state mutation orchestration

That makes it both too broad and too fragile to maintain safely.

### `compiler/parser_v2.py`

This parser is a major improvement over the legacy parser shape, but it still needs a clear boundary between:

- raw text lexing
- structural parsing
- alias resolution
- semantic object construction
- compatibility exports

It also contains Japanese strings in docstrings/comments, which means any future editing must preserve UTF-8 handling explicitly.

## Target Shape

### `engine/models/ability.py`

Make this module the schema and model boundary, not the “everything about abilities” module.

Keep here:

- `Ability`, `Effect`, `Cost`, `Condition`, and other core model types
- small accessors and convenience methods that only operate on model data
- stable serialization helpers that do not require parser/compiler knowledge

Move out:

- description tables
- packed filter helpers
- compiler/emission helpers
- semantic/IR conversion helpers
- any logic that is really about parsing or rendering rather than modeling

Suggested destinations:

- `engine/models/ability_descriptions.py`
- `engine/models/ability_filter.py`
- `engine/models/ability_ir.py`
- `compiler/ability_compile.py`
- `compiler/ability_emit.py`
- `compiler/ability_describe.py`

### `engine/game/mixins/effect_mixin.py`

Treat this as a compatibility surface, not the authoritative engine.

Keep here only if Python compatibility still needs it:

- thin orchestration wrappers
- compatibility entry points used by older callers
- minimal delegation to helper functions

Move out:

- cost evaluation
- choice handling
- condition checks
- effect resolution branching
- opcode dispatch
- state mutation logic

Suggested destinations:

- Rust interpreter handler modules in `engine_rust_src/src/core/logic/interpreter/handlers/`
- temporary Python helper modules only when a behavior has not yet been ported

### `compiler/parser_v2.py`

Make this module a layered parser rather than a single all-purpose parser implementation.

Keep here:

- parser entry points
- public compatibility exports
- top-level parse orchestration

Move out:

- low-level scanning/lexing
- alias tables
- effect grammar fragments
- target/condition/cost normalization helpers
- serialization/pretty-printing support

Suggested destinations:

- `compiler/parser_lexer.py`
- `compiler/parser_patterns.py`
- `compiler/parser_semantics.py`
- `compiler/parser_compat.py`

## Refactor Phases

### Phase 1: Lock the Encoding Boundary

Before any further movement of Japanese text or description tables:

- ensure every read/write path uses UTF-8 explicitly
- avoid copy/pasting through terminal output
- avoid extracting text with commands that can silently transliterate or garble Unicode
- preserve the source file encoding as UTF-8 end to end

Concrete rule:

- when moving non-ASCII content, use raw file reads and raw file writes, not console round-tripping

Validation rule:

- verify Japanese strings by reading the source files directly, not by trusting terminal-rendered output

### Phase 2: Split `ability.py` by Responsibility

1. Move all ability description strings into `engine/models/ability_descriptions.py`.
2. Move packed filter helpers into `engine/models/ability_filter.py`.
3. Keep the remaining file focused on model classes and stable schema behavior.
4. Extract compiler and rendering logic into dedicated compiler/model helper modules.
5. Add import shims only where the repo still depends on the old surface.

Exit criteria:

- `ability.py` reads like a model module, not a parser/compiler dump
- Japanese text is not interleaved with compiler logic
- filter packing is no longer embedded in the main model file

### Phase 3: Reduce `effect_mixin.py` to Orchestration

1. Identify the biggest logic clusters:
   - costs
   - choices
   - condition checks
   - effect resolution
   - movement/state mutations
2. Move each cluster into a focused helper or Rust handler.
3. Keep `effect_mixin.py` as a thin compatibility layer only if Python callers still require it.
4. Make new gameplay behavior land in Rust, not in Python.

Exit criteria:

- the mixin contains mostly delegation and compatibility glue
- new gameplay logic is not added to Python by default
- helpers have one clear owner each

### Phase 4: Layer `parser_v2.py`

1. Separate lexing from semantic parsing.
2. Move grammar fragments and regex patterns into their own module.
3. Move alias resolution and compatibility shims out of the parser core.
4. Keep the public parser API stable while the internals are decomposed.

Exit criteria:

- parsing phases are named and testable
- parser internals are easier to reason about
- compatibility imports remain intact

### Phase 5: Regression-Proof the Move

1. Add targeted tests around Japanese description strings.
2. Add tests that assert the parser still returns the same semantic objects.
3. Add tests for effect resolution compatibility where Python remains active.
4. Re-run full build/test flows after each extraction step.

Exit criteria:

- no text corruption after refactors
- parser behavior stays stable
- compatibility import paths continue to work

## Mojibake Fix Plan

The mojibake issue should be treated as an encoding hygiene problem, not as a content problem.

### Do

- read UTF-8 files as UTF-8
- write UTF-8 files as UTF-8
- preserve Japanese text directly in source files
- add `# -*- coding: utf-8 -*-` headers in modules that contain non-ASCII text if that improves clarity
- verify content from the file itself, not from terminal-encoded output

### Do Not

- do not copy Japanese text from garbled terminal output
- do not use a conversion step unless it is explicitly UTF-8-aware
- do not rely on console rendering to prove a file is correct

### Preferred move pattern

- extract text from the original file using raw file APIs
- write the extracted text into the destination file using raw file APIs
- confirm the destination file contains the expected Unicode code points

### Validation idea

- add a small test or check that asserts known Japanese phrases still exist in the expected modules
- treat any replacement character or corrupted glyphs as a failure

## Recommended Order

1. Finish the UTF-8-safe split of `ability.py`.
2. Pull `effect_mixin.py` down toward a thin compatibility layer.
3. Break `parser_v2.py` into lexer, semantics, and compatibility modules.
4. Add tests for the moved Japanese text and parser semantics.
5. Keep Rust as the primary runtime target for gameplay behavior.

## Notes

- This plan assumes the Rust engine is authoritative for live gameplay.
- The Python side should only keep what is still needed for compatibility, data modeling, or compiler support.
- The long-term goal is not just smaller files, but clearer ownership and safer text handling.
