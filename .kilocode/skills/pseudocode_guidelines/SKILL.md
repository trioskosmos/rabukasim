---
name: pseudocode_guidelines
description: Definitions, standards, and workflows for writing card ability pseudocode.
---

# Pseudocode Guidelines

> [!IMPORTANT]
> **Source of Truth**:
> - `data/consolidated_abilities.json` is the **ONLY** place to add or modify pseudocode.
> - **NEVER** edit `data/cards.json` directly for pseudocode, as it will be overwritten by the compiler or sync scripts.

## Core Workflow

1. **Locate Card**: Find the card ID using `tools/card_finder.py`.
2. **Edit Pseudocode**: Add or update the entry in `data/consolidated_abilities.json`.
3. **Compile**: Run `uv run python -m compiler.main` to apply changes to `cards_compiled.json`.
4. **Verify**: Use `tools/card_finder.py <ID>` to check the compiled bytecode.

## Syntax Standards

### Triggers
- `TRIGGER: ON_PLAY`
- `TRIGGER: ON_LIVE_START`
- `TRIGGER: ACTIVATED` (for Main Phase abilities)
- `TRIGGER: CONSTANT` (for passive effects)

### Effects
- **Play from Discard**: Use `PLAY_MEMBER_FROM_DISCARD(1)`. DO NOT use `SELECT_MEMBER` + `PLAY_MEMBER` separately.
  ```
  EFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_2"} -> TARGET
  ```

- **Look and Choose (Deck)**: Use `LOOK_AND_CHOOSE_REVEAL(X, choose_count=Y)`.
  - `X`: Number of cards to look at.
  - `choose_count=Y`: Number of cards to pick.
  - `REMAINDER="..."`: Destination for non-chosen cards.
    - `DISCARD`: Waiting Room (Compiled to `s` High Byte = 7).
    - `DECK`: Return to Deck/Shuffle (Default).
    - `HAND`: Add to Hand.
  ```
  EFFECT: LOOK_AND_CHOOSE_REVEAL(3, choose_count=1) {REMAINDER="DISCARD"} -> TARGET
  ```

- **Filters**: Use `{FILTER="..."}` params. Common filters:
  - `COST_LE_X` / `COST_GE_X`
  - `attribute` (e.g. `Pure`, `Cool`)
  - `IS_CENTER`

### Known Pitfalls
- **Compound Effects**: The compiler splits effects by `;`. Ensure parameters (like `ZONE`) are on the specific effect that needs them, or use a specialized opcode that implies the zone (like `PLAY_MEMBER_FROM_DISCARD`).
- **Opponent Targeting**: Use `TARGET="OPPONENT"` inside the effect parameters.

## Troubleshooting

If bytecode doesn't match expectation:
1. **Check Opcode Mapping**: See `compiler/patterns/effects.py` or `parser_v2.py`.
2. **Check Heuristics**: Some opcodes (like `PLAY_MEMBER`) use heuristics based on param text to decide the final opcode. Provide explicit context in params if needed.
