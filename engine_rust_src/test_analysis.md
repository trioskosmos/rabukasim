# Analysis of 23 Failing Tests

## Test Categories

### 1. Vienna Constant Stacking (2 tests)
Files: `qa::batch_card_specific`, `qa_verification_tests`
- Tests constant ability stacking behavior for Vienna card

### 2. look_and_choose (3 tests)
Files: `deck_refresh_tests`, `opcode_tests`
- `test_refresh_on_look_and_choose`
- `test_look_and_choose_source_zone_fix`
- `test_opcode_look_and_choose_filter_cost_ge`

### 3. Card 8844 Discard Tracking (2 tests)
- Discard tracking during activation branches

### 4. Cost Selection & Baton (4 tests)
- `test_q183_cost_selection_isolation`
- `test_q206_baton_touch_cost_reduction`
- Baton cost math and selection isolation issues

### 5. Heart Filter (1 test)
- `test_card_579_ability_1_heart_filter`

### 6. Card-Specific Issues (11 tests)
- Various card-specific behavior tests

## Likely Root Causes

1. **flow_helpers.rs consolidation** - The `current_effect()` function was simplified from 4 versions to 1. May have lost frame_idx-based lookup that some handlers depend on.

2. **models.rs changes** - `heart_counts()`, `heart_requirements()`, `look_choose()` now use decoder functions instead of manual bit extraction. May produce different values.

3. **Dispatch changes** - Simplified dispatch may not call handlers with correct parameters for all opcode types.

## Fix Plan

1. Restore frame_idx-based lookup in flow_helpers.rs if needed
2. Verify decoder functions match original manual extraction
3. Check dispatch logic for look_and_choose and other complex opcodes
4. Fix individual test issues systematically

## Files to Modify

1. `src/core/logic/interpreter/handlers/flow_helpers.rs`
2. `src/core/logic/models.rs`
3. `src/core/logic/interpreter/handlers/mod.rs`
4. Handler files for specific opcodes
