# Ability Frame Justification Progress

**Date**: In Progress  
**Status**: First pass - manually reviewing each ability  

## Summary

**Total abilities in JSON**: 614  
**Abilities documented so far**: ~15  
**Critical issues found**: 4

## Critical Issues Found & Documented

### 1. PL!N-pb1-005-P+ (宮下 愛) ab#0
- **Issue**: Empty GROUP_FILTER with no attributes
- **Problem**: Would trigger for ANY member, not cost 10 as text specifies
- **Fix Applied**: Replaced with proper COUNT_STAGE with value_threshold: 10

### 2. PL!HS-bp5-007-P (鬼塚夏美) ab#0
- **Issue**: SUCCESS_PILE_COUNT used instead of COUNT_STAGE
- **Problem**: Checked success pile instead of stage for year members
- **Fix Applied**: Replaced with COUNT_STAGE with group_id: "YEAR"

### 3. PL!HS-bp1-004-P (国木田花丸) ab#0
- **Issue**: GROUP_FILTER with value: 3 for "only" condition
- **Problem**: Checks for 3+ Aqours, not "only Aqours"
- **Status**: Documented, needs fix (COUNT_STAGE + SUM_VALUE pattern)

### 4. PL!-bp4-020-L (乙宗 梢) ab#0
- **Issue**: GROUP_FILTER with value: 4 for "only" condition
- **Problem**: Checks for 4+ Hasuno, not "only Hasuno"
- **Status**: Documented, needs fix

## Pattern of Common Issues Found

1. **Empty/broken GROUP_FILTER** - Missing attributes making condition meaningless
2. **Wrong zone targeting** - SUCCESS_PILE vs STAGE confusion
3. **"Only" condition bugs** - Using GROUP_FILTER with arbitrary value instead of proper comparison
4. **Missing target_player: SELF** - Could affect opponent's cards
5. **Missing JUMP_IF_FALSE** - After optional costs

## Abilities Documented in Detail

1. PL!S-bp2-004-P/R (黒澤ダイヤ) - META_RULE deck construction
2. Shared: ON_PLAY Draw+Discard - Multiple N cards
3. Shared: Optional Discard + Scout - 12+ cards
4. PL!HS-bp1-004-P (国木田花丸) - With "only" bug
5. PL!SP-bp4-025-L (Special Color) ab#0 - Center blade transform
6. PL!SP-bp4-025-L ab#1 - Center moved check
7. PL!SP-bp5-001-AR (渋谷かのん) ab#2 - OR cost pattern
8. PL!SP-bp4-027-L (Chance Day, Chance Way!) - "Only Liella!" check
9. PL!N-pb1-005-P+ (宮下 愛) - FIXED critical bug
10. PL!-pb1-015-P+ (西木野真姫) - Center tap/discard
11. PL!HS-bp5-007-P (鬼塚夏美) - FIXED success pile bug
12. PL!HS-bp5-013-N (村野さやか) - Unique cost NOP pattern
13. PL!-sd1-014-SD (星空凛) - Simple draw 1
14. PL!-bp4-020-L (乙宗 梢) - With "only" bug
15. PL!-sd1-011-SD etc - Look and choose pattern

## Continuing Work

The process is:
1. Read ability from JSON
2. Analyze text vs frames
3. Document justification
4. Note any issues
5. Fix critical bugs immediately
6. Move to next ability

## Next Steps

Continue through all remaining ~600 abilities, then do second pass for verification.
