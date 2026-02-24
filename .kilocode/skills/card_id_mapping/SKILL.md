# Card ID Mapping Skill

This skill handles the translation between legacy card IDs (used in test scenarios) and the current logic IDs used by the LovecaSim Rust engine.

## Context
The project recently migrated to a new ID system. Test scenarios in `engine_rust_src/data/scenarios.json` still use "Old IDs" (represented by `real_card_id`). These must be mapped to "Logic IDs" for the engine to correctly identify cards.

## Source of Truth
- **Mapping Report**: [id_migration_report.txt](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/reports/id_migration_report.txt)
- **Old IDs**: [old_id_map.json](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/reports/old_id_map.json)
- **New IDs**: [new_id_map.json](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/reports/new_id_map.json)

## Mapping Logic
1.  **Bridging via Card No**: The `real_card_id` in `scenarios.json` can be inconsistent with the current migration report due to minor dataset changes. The most robust bridge is the `Card No` found in the `scenario_name` (e.g., `PL!N-pb1-001-P＋`).
2.  **Conversion Path**: `scenario.scenario_name` -> Extract `Card No` -> `new_id_map.json` -> `Logic ID`.
3.  **Special Cases**:
    - Member cards: Use `new_id_map.json`.
    - Live cards: Old IDs often >= 30000. Extract number (e.g. `PL!-bp3-020-L`) from name and map.
    - Energy: Old IDs 40000 range -> Logic ID 40000 range (usually consistent).

## Implementation Strategy
- Pre-generate a mapping: `Old ID` -> `Logic ID` by iterating through all scenarios and applying the bridging logic.
- Use this map in `archetype_runner.rs` to setup zones.
