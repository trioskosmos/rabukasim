# Card 162 (安養寺 姫芽) - Fix Summary

## Issues Fixed

### 1. **Optional Flag Issue**
- **Before:** `MOVE_TO_DISCARD(3) (Optional)` - incorrectly marked as optional
- **After:** `MOVE_TO_DISCARD(3)` - correctly mandatory
- **Impact:** The ability should FORCE discard of 3 cards, not give the player a choice to skip

### 2. **Heart Type Mismatch**
- **Before:** `ADD_HEARTS(1) {HEART_TYPE=1}`
- **After:** `ADD_HEARTS(1) {HEART_TYPE=0}`
- **Impact:** Changed from heart_type=1 to heart_type=0 (HEART_PINK/red) to match the carnal condition

### 3. **Condition Filter Mismatch**
- **Before:** `CONDITION: ALL_MEMBERS {FILTER="HEART_01", ZONE="DISCARDED_THIS"}`
- **After:** `CONDITION: ALL_CARDS_MATCH {FILTER="HEART_PINK, TYPE_MEMBER", ZONE="DISCARDED_THIS"}`
- **Impact:** Corrected the condition to properly check for HEART_PINK members that were discarded

## Bytecode Changes

### Before Fix
```
Bytecode: [58, 3, 1, 536870912, 65540, ...]
Effect 0: Type=58, Value=3, Optional=True, heart_type=1
```

### After Fix
```
Bytecode: [58, 3, 1, 0, 65540, ...]
Effect 0: Type=58, Value=3, Optional=False, heart_type=0
```

Key bytecode position changes:
- **Index 3:** `536870912` → `0` (removed optional flag)
- **Index 12:** `1` → `0` (fixed heart type)

## Files Modified

1. **data/consolidated_abilities.json** - Updated pseudocode for card 162
   - Removed `(Optional)` flag from MOVE_TO_DISCARD
   - Changed condition from `ALL_MEMBERS` to `ALL_CARDS_MATCH`
   - Changed `HEART_TYPE=1` to `HEART_TYPE=0`

2. **data/cards_compiled.json** - Recompiled with corrected bytecode
   - Compiled via `python -m compiler.main`

3. **engine_rust_src/src/repro/test_card_162_fix.rs** - Added verification test
   - Verifies bytecode structure has correct values
   - Confirms mandatory nature of ability
   - Confirms proper heart type

4. **engine_rust_src/src/repro/mod.rs** - Added test module

## Verification

✓ Compilation: `python -m compiler.main` - All 1787 cards compiled successfully
✓ Rust codegen: `python tools/codegen_abilities.py` - 21 abilities generated
✓ Unit test: `test_card_162_anyoji_himeme_discard_3_cards` - PASSES
✓ Engine tests: 597 passing (1 unrelated failure pre-existing: Q223)

## Official Card Details

- **Card ID:** 162
- **Card No:** PL!HS-PR-021-PR (also PL!HS-PR-021-RM ID:684)
- **Name:** 安養寺 姫芽
- **Trigger:** ON_PLAY
- **Effect:** MOVE_TO_DISCARD(3) from DECK_TOP (mandatory)
- **Condition:** ALL members in discarded pile must have HEART_PINK
- **Result:** Gain 1 HEART_RED until end of live
