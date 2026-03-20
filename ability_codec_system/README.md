# Ability Codec System

This folder holds the new ability inspection and conversion layer for the project.

The goal is to move away from treating abilities as opaque bytecode blobs and instead expose a sparse, readable model that can still round-trip back to the original 5-word frame layout.

## What it does

- Decodes `data/cards_compiled.json` abilities into sparse frames.
- Uses `data/metadata.json` to name opcodes, conditions, costs, triggers, targets, slots, and action bases.
- Preserves round-trip safety for the current bytecode layout.
- Rebuilds choice/mode branches as nested `choices` blocks instead of leaving them only as flat `SELECT_MODE` + `JUMP` control flow.
- Marks negated `1xxx` condition frames explicitly with `negated: true`.

## Current model

The current frame model is intentionally sparse:

- `opcode`
- `opcode_id`
- `opcode_section`
- `value` when meaningful
- `attr` when meaningful
- `slot` when meaningful
- `negated` for wrapped negation frames
- `decoded` for human-readable text
- `metadata_refs` for the source labels

For modal or branching abilities, the codec also emits:

- `choices`
- `selector_frame_index`
- `option_count`
- `jump_table`
- `options[].frames`

That gives us a branch-aware view without losing the underlying linear bytecode representation.

## Important encoding rules

- Plain opcodes use their normal metadata names.
- `1xxx` values are treated as negated condition wrappers when the base id matches a known condition or opcode.
- `action_bases` in `metadata.json` are still a separate namespace and should not be confused with the negation wrapper.
- Unknown ids still fall back to `OP_<id>`.

## Example

The card `Bloom the smile, Bloom the dream!` is now represented as a branch-aware choice block:

- `SELECT_MODE`
- one `JUMP` per option
- nested option bodies

The same ability can still be flattened back into the original frame sequence when serializing.

## Files

- [`tools/bytecode_codec.py`](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/bytecode_codec.py)
- [`tools/consolidate_abilities.py`](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/consolidate_abilities.py)
- [`engine_rust_src/src/bin/rewrite_ability_index.rs`](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/src/bin/rewrite_ability_index.rs)
- [`data/ability_frame_index.json`](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_index.json)
- [`backend/tests/test_bytecode_codec.py`](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/backend/tests/test_bytecode_codec.py)
- [`backend/tests/test_consolidate_abilities.py`](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/backend/tests/test_consolidate_abilities.py)
- [`backend/tests/test_bytecode_catalog.py`](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/backend/tests/test_bytecode_catalog.py)

## How to run

From the repo root:

```powershell
.\.venv\Scripts\python.exe ability_codec_system\tests\test_bytecode_codec.py
.\.venv\Scripts\python.exe ability_codec_system\tests\test_consolidate_abilities.py
.\.venv\Scripts\python.exe ability_codec_system\tests\test_bytecode_catalog.py
```

If you want to regenerate the index or the supporting outputs:

```powershell
.\.venv\Scripts\python.exe tools\consolidate_abilities.py
.\.venv\Scripts\python.exe engine_rust_src\src\bin\rewrite_ability_index.rs
```

## What is still left

- More branch patterns beyond `SELECT_MODE` should be lifted into the nested model.
- The human-readable renderer should prefer the branch-aware view everywhere.
- The remaining `1xxx` cases should be continuously checked so they stay classified as negated conditions and not mistaken for action-base ids.
- If we want to author new cards directly in the sparse model, we still need a first-class sparse-to-bytecode encoder for all opcode families.

## Steps from here

1. Keep the sparse index as the inspection source of truth.
2. Expand the branch-aware conversion beyond modal choices.
3. Finish pushing the human-readable output to show nested choice blocks.
4. Add a full sparse authoring schema only after the common frame families are stable.
## Roadmap

See [PLAN.md](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/ability_codec_system/PLAN.md) for the full writable-system roadmap:

- semantic authoring schema
- opcode reference generation
- full semantic-to-bytecode encoder
- validation and round-trip tests
- migration phases and success criteria
