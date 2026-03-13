---
name: pseudocode_guidelines
description: "[CONSOLIDATED] - See ability_compilation_bytecode/SKILL.md instead"
---

# ⚠️ Deprecated - See ability_compilation_bytecode

This skill has been **consolidated** into a unified framework.

**New Location**: `.agent/skills/ability_compilation_bytecode/SKILL.md`

**Consolidated Content** (now in Part 1):
- Core workflow
- Syntax standards (triggers, effects, filters)
- Reference keywords
- Pseudocode mapping tables
- Known pitfalls & troubleshooting

**Consolidated With**:
- ability_logic (semantic verification, bytecode tools)
- opcode_management (metadata, bitpacking standards)
- Version gating (bytecode layout v1/v2)
- Parity testing (IR ↔ bytecode ↔ readable)
- Shared bytecode decoders

**Reason**: Pseudocode is just the first step in ability compilation. The full workflow spans:
1. Write pseudocode (consolidated Part 1)
2. Manage opcodes (Part 2)
3. Version bytecode layout (Part 3)
4. Test parity (Part 4)
5. Use shared decoders (Part 5)
6. Access semantic forms (Part 6)
7. Debug & audit (Part 7)

Keeping them separate created friction and duplication.

**Action**: Update any references to use `.agent/skills/ability_compilation_bytecode/` instead.

---

## Reference (Legacy)

*The content below is preserved as reference but superseded by the consolidated skill.*

# Pseudocode Guidelines

> [!IMPORTANT]
> **Source of Truth**:
> - `data/consolidated_abilities.json` is the **ONLY** place to add or modify pseudocode.
> - **NEVER** edit `data/cards.json` or `data/manual_pseudocode.json` directly for pseudocode, as they are legacy or master-data only.

## Core Workflow

1. **Instant Lookup & Triage**: Use `tools/test_pseudocode.py --card <ID>` to see current name, JP text, and compiled logic.
2. **Rapid Iteration**: Test new pseudocode ideas instantly with `uv run python tools/test_pseudocode.py "..."`.
3. **Reference Keywords**: If unsure of syntax, run `uv run python tools/test_pseudocode.py --reference` to see all valid triggers/effects and their parameters.
4. **Finalize**: Add the verified pseudocode to `data/consolidated_abilities.json`.
5. **Full Compile**: Run `uv run python -m compiler.main` to sync the master data.

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
