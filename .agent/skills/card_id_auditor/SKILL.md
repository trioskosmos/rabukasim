---
name: card_id_auditor
description: Unified skill for auditing and verifying card IDs against the master database.
---

# Card ID Auditor Skill

This skill provides a structured way to verify that card IDs used in tests and logic align with the unified bit-packed ID system (12 bits for logic ID, 4 bits for variant index).

## Core Principles

1.  **Unified Encoding**: Always use `(logic_id & 0x0FFF) | (variant_idx << 12)` for card IDs.
2.  **Logic ID Range**: Logical IDs must be within [0, 4095].
3.  **Variant Range**: Variant indices must be within [0, 15].
4.  **Source of Truth**: `data/cards_compiled.json` is the authoritative source for all card metadata and IDs.
5.  **Logic ID Separation**: While the engine supports logic IDs 0-4095 for both Member and Live cards, official data maintains strictly separate Logic ID sets for each type within `members_vec` and `lives_vec`.
6.  **Safe Test Ranges**: When creating dummy cards in tests, use Logic IDs in the [3000-3999] range to avoid collisions with official card data (0-1500).

## Workflows

### 1. Verification of Test IDs
When writing or debugging tests:
- Check if the IDs used in the test (e.g., `deck`, `stage`, `discard`) are registered in the `CardDatabase` returned by `create_test_db`.
- If using dummy IDs, ensure they are registered in a local `CardDatabase` for that test.

### 2. ID Mapping Audit
To verify a specific card's packed ID:
- Use `tools/card_finder.py <CARD_NO>` to get the official ID.
- Manually calculate: `PackedID = LogicID + (Variant * 4096)`.

## Common Pitfalls
- **Missing Registration**: Cards in `deck` or `hand` that are not in the `CardDatabase` will cause "Card not found" errors during trigger checks.
- **Index Out of Bounds**: `logic_id` >= 4096 will crash if accessed via `members_vec` or `lives_vec`.
- **Mismatched IDs**: Using raw IDs from `cards.json` without verifying if the compiler mapped them differently.
