---
name: card_data
description: Consolidated skill for card data lookup, ID auditing, and mapping.
---

# Card Data Skill

This skill provides a unified entry point for finding card information, auditing IDs, and mapping legacy data.

## 🔍 Card Search & Lookup
The primary tool is `tools/cf.py`. It supports:
- **Card Number**: `PL!S-bp2-005-P`
- **URL**: Extracted from card image URLs.
- **Engine IDs**: Packed (16-bit) or Logic (0-4095).
- **Text**: Searches within metadata.
- **Cross-References**: Automatically finds related Q&A rulings and **Ability Frames**.

### 🛡️ Report-Based Workflow (Recommended)
**ALWAYS** generate a report and read it via `view_file`. This avoids Japanese character corruption in the terminal and provides a persistent, readable record.
1. **Generate**:
   ```bash
   uv run python tools/cf.py "<INPUT>" --output reports/card_analysis.md
   ```
2. **Read**:
   Use `view_file` on the generated markdown file in the `reports/` directory.

### 🧪 Frame & Signature Inspection
If you need to see the exact logic the card uses:
- **In Report**: Check the "Ability Frames" section. It shows the `signature` and the decoded frame sequence (e.g., `DRAW`, `RECOVER_LIVE`).
- **In JSON**: Use the `--json` flag to see the raw `frame_program` and `signature` fields:
  ```bash
  uv run python tools/cf.py "<INPUT>" --json
  ```

> [!TIP]
> This is the most reliable way to inspect card logic, frames, and related QA rulings without needing to decode legacy runtime encodings.

## 🆔 ID System Standards
- **Unified Encoding**: `(logic_id & 0x0FFF) | (variant_idx << 12)`.
- **Logic ID Range**: `[0, 4095]`.
- **Safe Test IDs**: Use `[3000-3999]` for dummy cards to avoid collisions with official data `(0-1500)`.
- **Primary Authored Ability Source**: `data/ability_frame_index.yaml`.
- **Primary Derived Runtime Ability View**: `data/consolidated_abilities.json`.
- **Frame Program Field**: the JSON output exposes `frame_program` for executable logic and `signature` for lookup.

## 🗺️ Legacy ID Mapping
Test scenarios often use "Old IDs" (`real_card_id`). Bridge them via `Card No`:
1. Extract `Card No` from scenario name (e.g., `PL!N-pb1-001-P＋`).
2. Match in `new_id_map.json` to get the current `Logic ID`.

### Reference Files
- [new_id_map.json](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/reports/new_id_map.json)
- [id_migration_report.txt](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/reports/id_migration_report.txt)

## ⚠️ Common Pitfalls
- **Ignoring Signatures**: Assuming two cards have the same logic because they look similar. Always check the `signature`.
- **Mismatched IDs**: Using raw `cards.json` IDs instead of compiled ones.
- **Variant Desync**: Variant `0`=Base, `1`=R+, `2`=P+.
