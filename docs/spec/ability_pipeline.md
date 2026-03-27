# Ability Pipeline

This document describes the active ability pipeline used by the project today.

## Current flow

1. `data/cards.json` is the authored card source.
2. `tools/abilities/pipeline.py` decides whether the compiled assets are stale and then calls `compiler.main.compile_cards()`.
3. `compiler/main.py` builds `MemberCard` and `LiveCard` objects through `parse_member()` and `parse_live()`.
4. Those functions call `_resolve_abilities()` to load ability frame data from the sparse frame index.
5. `engine.models.ability.Ability.to_frame_program()` returns the canonical frame program for each ability.
6. `compiler.main._compile_abilities_for_export()` now normalizes cached frame programs and semantic form data instead of regenerating legacy bytecode.
7. The result is written to `data/cards_compiled.json` and synced to `engine/data/cards_compiled.json`.
8. At runtime, `engine/game/data_loader.py` loads the compiled database and attaches `sparse_frame_index` data to each ability.

## Important detail

`compiler/parser_v2.py` still exists, but it is no longer the main pipeline.
It is kept for compatibility and tooling, while the real path now runs through the authored frame data and `Ability.to_frame_program()`.

## Main entry points

- Build orchestration: [`tools/abilities/pipeline.py`](../../tools/abilities/pipeline.py)
- Compiler entry: [`compiler/main.py`](../../compiler/main.py)
- Ability model: [`engine/models/ability.py`](../../engine/models/ability.py)
- Runtime loader: [`engine/game/data_loader.py`](../../engine/game/data_loader.py)

