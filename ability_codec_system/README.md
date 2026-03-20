# Ability Codec System

This folder groups the new bytecode-oriented ability tooling in one place.

## What It Contains

- `bytecode_codec.py`
  - Two-way codec for `bytecode -> annotated frame model -> bytecode`
  - Uses `metadata.json` to name opcodes, triggers, slots, and other fields
  - Preserves raw 5-word frames for exact round-tripping

- `consolidate_abilities.py`
  - Builds a sparse ability index from compiled card data
  - Groups abilities by stable `trigger + bytecode` signature
  - Records every card that uses each unique ability
  - Writes `data/ability_frame_index.json`
  - Each frame only stores active words/fields, not zero fillers

- `bytecode_catalog.py`
  - Produces a bytecode atlas / report view
  - Annotates each 5-word frame with metadata and code references
  - Useful for debugging and comparing bytecode shapes across cards

- `tests/`
  - `test_bytecode_codec.py`
  - `test_consolidate_abilities.py`
  - `test_bytecode_catalog.py`

## Intended Workflow

1. Decode compiled abilities into a readable frame model.
2. Reduce each frame to only the active words/fields.
3. Re-encode that model and confirm the bytecode matches.
4. Build the sparse ability index from compiled cards.
5. Use the catalog and tests to keep the mapping stable.

## How To Run

From the repo root:

```powershell
.\.venv\Scripts\python.exe ability_codec_system\tests\test_bytecode_codec.py
.\.venv\Scripts\python.exe ability_codec_system\tests\test_consolidate_abilities.py
.\.venv\Scripts\python.exe ability_codec_system\tests\test_bytecode_catalog.py
.\.venv\Scripts\python.exe ability_codec_system\consolidate_abilities.py
.\.venv\Scripts\python.exe ability_codec_system\bytecode_catalog.py
```

## Notes

- The root `tools/` and `backend/tests/` files still exist for compatibility.
- This folder is the organized home for the new system, not a separate rewrite.
- The system is intentionally conservative: exact bytecode preservation first, semantics later.
