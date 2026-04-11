# Ability Frame Fixes - Complete Summary

## Overview
A comprehensive analysis and fix of all 614 abilities in `ability_frame_source.json` was completed. 

## Statistics
- **Total abilities scanned**: 614
- **Abilities modified**: 89
- **Total fixes applied**: 156
- **Tests added**: 10 new Rust test groups

## Fix Categories Applied

### 1. `target_player: SELF` additions (74 fixes)
**Problem**: Abilities checking "自分のステージ" were missing `target_player: SELF`, potentially affecting opponent's stage.

**Solution**: Added `target_player: SELF` to all relevant COUNT_STAGE, GROUP_FILTER, and SELECT_MEMBER frames.

**Example**:
```json
// Before
{"op": "COUNT_STAGE", "slot": {"target_slot": "STAGE_0"}}

// After
{"op": "COUNT_STAGE", "attr": {"target_player": "SELF"}, "slot": {"target_slot": "STAGE_0"}}
```

### 2. Group filter fixes (27 fixes)
**Problem**: Abilities mentioning specific groups (Liella!, μ's, Aqours, 虹ヶ咲) lacked proper group filters.

**Solution**: Added `group_enabled: 1` and `group_id` attributes.

**Example**:
```json
// Card checking for Liella! members
{"attr": {"group_enabled": 1, "group_id": "LIELLA"}}
```

### 3. `is_optional` flag fixes (18 fixes)
**Problem**: Optional actions (marked by "してもよい" in text) were not marked as optional in frames.

**Solution**: Added `is_optional: 1` to FORMATION_CHANGE, MOVE_TO_DISCARD, etc.

### 4. Missing `JUMP_IF_FALSE` additions (15 fixes)
**Problem**: Condition checks and optional costs weren't followed by proper flow control.

**Solution**: Added `JUMP_IF_FALSE` frames to skip effects when conditions fail or costs aren't paid.

**Pattern**:
```json
[
  {"op": "COUNT_STAGE", ...},      // Check condition
  {"op": "JUMP_IF_FALSE", "value": 1}, // Skip if failed
  {"op": "EFFECT", ...},            // Only executes if condition met
  {"op": "RETURN"}
]
```

### 5. `SELECT_MEMBER` → `COUNT_STAGE` conversions (12 fixes)
**Problem**: Abilities with automatic conditions ("center area") were using player-choice `SELECT_MEMBER`.

**Solution**: Replaced with `COUNT_STAGE` for automatic detection.

**Example** - Special Color ab#0:
```json
// Before: Player selects center member
{"op": "SELECT_MEMBER", "slot": {"target_slot": "CONTEXT", "area_idx": 2}}

// After: Automatic center area check
{"op": "COUNT_STAGE", "attr": {"target_player": "SELF", ...}, "slot": {"target_slot": "STAGE_2"}}
```

### 6. Movement check additions (4 fixes)
**Problem**: Abilities checking "このターン中に移動している" lacked the movement flag.

**Solution**: Added `check_moved_this_turn: 1` attribute.

### 7. Zone/area fixes (6 fixes)
**Problem**: Some frames used wrong target slots for specific areas.

**Solution**: Fixed `target_slot` to use `STAGE_2` for center area, etc.

## Files Created/Modified

### Data Files
- `data/ability_frame_source.json` - Modified with 156 fixes across 89 abilities
- `data/ability_frame_source.json.backup` - Automatic backup created

### Analysis Scripts
- `data/analyze_all_abilities.py` - Initial analysis script
- `data/fix_abilities.py` - First round of fixes
- `data/deep_ability_scan.py` - Comprehensive deep scan
- `data/apply_deep_fixes.py` - Automated fix application

### Reports
- `docs/ability_analysis_report.md` - Initial analysis (61KB)
- `docs/ability_fixes_report.md` - First fix report
- `docs/ability_fixes_detailed.md` - Detailed fix explanations
- `docs/deep_ability_scan_report.md` - Deep scan results (111KB)
- `docs/deep_fixes_applied.md` - Final fix listing
- `docs/ABILITY_FIXES_SUMMARY.md` - This summary

### Test Files
- `engine_rust_src/src/test_suite/ability_fixes_tests.rs` - 10 test groups covering all fix types

## Notable Fixes by Card

### PL!SP-bp4-025-L (Special Color)
- **ab#0**: Fixed center area auto-detection (SELECT_MEMBER → COUNT_STAGE)
- **ab#1**: Added movement check flag for "moved this turn" condition

### PL!SP-bp5-001-AR (Shibuya Kanon)
- **ab#2**: Added SELECT_MODE pattern for OR cost (tap OR discard)

### PL!SP-bp4-027-L (Chance Day, Chance Way!)
- **ab#0**: Fixed "only Liella!" condition with proper COUNT_STAGE pattern

### Multiple cards with "自分のステージ"
- Added `target_player: SELF` to 74 frames across various cards

## Test Coverage

The new Rust tests cover:
1. ✅ `target_player: SELF` verification
2. ✅ Optional cost + JUMP_IF_FALSE flow
3. ✅ Center area COUNT_STAGE pattern
4. ✅ Group filter specification
5. ✅ OR cost SELECT_MODE pattern
6. ✅ Movement check conditions
7. ✅ Optional formation change
8. ✅ "Only" condition patterns
9. ✅ Specific fixed card regression tests
10. ✅ Edge cases (condition not met, skip all OR options)

## Validation

All changes were validated for:
- ✅ JSON structure validity
- ✅ Sequential frame indices
- ✅ No duplicate indices
- ✅ All card_refs preserved
- ✅ Consistent attribute types

## Remaining Manual Review Required

The following patterns were flagged but require manual review:

### 1. Complex "only" conditions (3 abilities)
Cards using GROUP_FILTER with arbitrary values for "only" conditions need structural changes:
- PL!-pb1-002-P+#Ab0: "μ'sのみ" but uses GROUP_FILTER value=4
- PL!SP-bp4-001-P#Ab0: Group filter with "only" condition
- PL!-bp4-020-L#Ab0: "Liella!のみ" check

**Recommended fix**: Convert to COUNT_STAGE sequence:
```json
[
  {"op": "COUNT_STAGE", "attr": {"group_id": "LIELLA"}},  // Count group
  {"op": "SUM_VALUE"},                                      // Accumulate
  {"op": "COUNT_STAGE"},                                     // Count total
  {"op": "SUM_VALUE", "slot": {"comparison": "EQ"}},       // Compare equal
  {"op": "JUMP_IF_FALSE", "value": 1},                      // Skip if not "only"
  {"op": "EFFECT"},
  {"op": "RETURN"}
]
```

### 2. Complex OR costs
Some OR costs may need more sophisticated branching than the simple SELECT_MODE pattern can handle.

## How to Run Tests

```bash
cd engine_rust_src
cargo test ability_fixes
```

To run all tests:
```bash
cargo test
```

## Future Recommendations

1. **Implement runtime checks** for new attributes like `check_moved_this_turn`
2. **Add more edge case tests** for complex branching patterns
3. **Review remaining 3 abilities** with "only" condition patterns
4. **Consider automated frame validation** on JSON changes
5. **Add integration tests** testing full card playthroughs

## Contact

For questions about specific fixes, refer to:
- `docs/deep_fixes_applied.md` for complete fix listing
- `docs/deep_ability_scan_report.md` for detailed issue analysis
- `engine_rust_src/src/test_suite/ability_fixes_tests.rs` for test implementations
