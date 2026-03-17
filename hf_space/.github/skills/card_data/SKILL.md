---
name: card_data
description: Consolidated skill for card data lookup, ID auditing, and mapping.
---

# Card Data Skill

This skill provides a unified entry point for finding card information, auditing IDs, and mapping legacy data.

## 🔍 Card Search & Lookup
The primary tool is `tools/card_finder.py`. It supports:
- **Card Number**: `PL!S-bp2-005-P`
- **URL**: Extracted from card image URLs.
- **Engine IDs**: Packed (16-bit) or Logic (0-4095).
- **Text**: Searches within metadata.
- **Cross-References**: Automatically finds related Q&A rulings and Rust tests.

### 🛡️ Report-Based Workflow (Recommended)
**ALWAYS** generate a report and read it via `view_file`. This avoids Japanese character corruption in the terminal and provides a persistent, readable record.
1. **Generate**:
   ```bash
   uv run python tools/card_finder.py "<INPUT>" --output reports/card_analysis.md
   ```
2. **Read**:
   Use `view_file` on the generated markdown file in the `reports/` directory.

### 🧩 Raw JSON Inspection
If you need to see the exact structure the engine uses (compiled bytecode, packed attributes, etc.):
- **In Report**: Check the "Raw Compiled JSON Data" section at the end of the markdown file.
- **In Terminal**: Use the `--json` flag for a clean stdout dump:
  ```bash
  uv run python tools/card_finder.py "<INPUT>" --json
  ```

> [!TIP]
> This is the most reliable way to inspect card logic, opcodes, and raw attribute bits without truncation or encoding issues.

> [!TIP]
> This is the most reliable way to inspect card logic, opcodes, and related QA rulings without truncation or encoding issues.

## 🆔 ID System Standards
- **Unified Encoding**: `(logic_id & 0x0FFF) | (variant_idx << 12)`.
- **Logic ID Range**: `[0, 4095]`.
- **Safe Test IDs**: Use `[3000-3999]` for dummy cards to avoid collisions with official data `(0-1500)`.
- **Source of Truth**: `data/cards_compiled.json`.

## 🗺️ Legacy ID Mapping
Test scenarios often use "Old IDs" (`real_card_id`). Bridge them via `Card No`:
1. Extract `Card No` from scenario name (e.g., `PL!N-pb1-001-P＋`).
2. Match in `new_id_map.json` to get the current `Logic ID`.

### Reference Files
- [new_id_map.json](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/reports/new_id_map.json)
- [id_migration_report.txt](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/reports/id_migration_report.txt)

## ⚠️ Common Pitfalls
- **Missing Registration**: Cards in zones that aren't in `create_test_db` will crash.
- **Mismatched IDs**: Using raw `cards.json` IDs instead of compiled ones.
- **Variant Desync**: Variant `0`=Base, `1`=R+, `2`=P+.
