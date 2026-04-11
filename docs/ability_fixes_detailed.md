# Detailed Ability Frame Fixes

## Summary
- **Total abilities analyzed**: 614
- **Abilities with issues found**: 138
- **Total fixes applied**: 66 abilities modified with 81 fixes

## Common Issue Patterns Fixed

### 1. Missing `target_player: SELF`
**Problem**: Abilities checking "自分のステージ" (your stage) were missing `target_player: SELF`, which could cause them to affect opponent's stage.

**Fix**: Added `target_player: SELF` to all relevant frames.

**Examples**:
- PL!HS-bp2-005-P#Ab0: Frame 3 - COUNT_STAGE for own stage check
- PL!-bp3-004-P#Ab0: Frame 0 - SELECT_MEMBER from own stage
- PL!N-pb1-012-P+#Ab0: Frame 0 - GROUP_FILTER on own stage

### 2. Incorrect `is_optional` on Mandatory Costs
**Problem**: Some abilities had `is_optional: 1` on costs that were mandatory (no "もよい" / "may" in text).

**Fix**: Removed `is_optional` from mandatory cost frames.

**Examples**:
- PL!HS-bp5-013-N#Ab0: MOVE_TO_DISCARD was marked optional but text requires discarding
- PL!N-bp5-014-N#Ab0: Mandatory cost incorrectly flagged as optional
- PL!HS-PR-019-PR#Ab0: Frame 0 - Removed incorrect is_optional

### 3. Missing `JUMP_IF_FALSE` After Optional Costs
**Problem**: Optional costs like `MOVE_TO_DISCARD` with `is_optional: 1` were not followed by `JUMP_IF_FALSE`, causing the effect to execute even when cost wasn't paid.

**Fix**: Added `JUMP_IF_FALSE` frame after optional costs.

**Examples**:
- PL!HS-bp1-005-P#Ab0: Added JUMP_IF_FALSE after optional MOVE_TO_DISCARD
- PL!HS-PR-016-PR#Ab0: Added JUMP_IF_FALSE after optional cost
- PL!HS-PR-017-PR#Ab0: Added JUMP_IF_FALSE after optional cost

### 4. Missing Movement Check
**Problem**: Abilities with "このターン中に移動している" (moved this turn) condition were missing the `check_moved_this_turn` flag.

**Fix**: Added `check_moved_this_turn: 1` to relevant frames.

**Example**:
- PL!SP-pb1-025-L#Ab0: Added check_moved_this_turn flag for "moved this turn" condition

### 5. GROUP_FILTER "only" Pattern Issues
**Problem**: Abilities with "のみ" (only) condition were using `GROUP_FILTER` with arbitrary values (3, 4) instead of properly checking ALL members are in the group.

**Identified but not auto-fixed** (requires structural changes):
- PL!-pb1-002-P+#Ab0: GROUP_FILTER value=4 but should check all members are in group
- PL!SP-bp4-001-P#Ab0: GROUP_FILTER value=3 but text says "only"
- PL!-bp4-020-L#Ab0: GROUP_FILTER value=4 with "only" condition

**Correct Pattern**: Should use `COUNT_STAGE` (group members) → `SUM_VALUE` (compare) → `COUNT_STAGE` (total members) → `JUMP_IF_FALSE` sequence.

## Frame Logic Explanations

### SELECT_MEMBER vs COUNT_STAGE
- **SELECT_MEMBER**: Use when player needs to choose a specific member
- **COUNT_STAGE**: Use when checking automatic conditions (center area, "only" conditions)

### JUMP_IF_FALSE Placement
After optional costs:
```
PAY_ENERGY (is_optional: 1) → JUMP_IF_FALSE → EFFECT → RETURN
```

After condition checks:
```
COUNT_STAGE (check condition) → JUMP_IF_FALSE (skip if failed) → EFFECT → RETURN
```

### Target Player Specification
Always include `target_player: SELF` when:
- Text says "自分のステージ" (your stage)
- Effect should only affect your cards
- Checking conditions on your side of play

## Files Modified

The following 66 abilities were fixed in `ability_frame_source.json`:

1. PL!HS-bp1-005-P#Ab0 - Added JUMP_IF_FALSE
2. PL!HS-bp5-013-N#Ab0 - Removed incorrect is_optional
3. PL!N-bp5-014-N#Ab0 - Removed incorrect is_optional
4. PL!S-bp5-014-N#Ab0 - Removed incorrect is_optional
5. PL!S-bp5-015-N#Ab0 - Removed incorrect is_optional
6. PL!HS-bp2-005-P#Ab0 - Added target_player: SELF
7. PL!-bp3-004-P#Ab0 - Added target_player: SELF
8. PL!-bp3-009-P#Ab0 - Added target_player: SELF
9. PL!N-pb1-012-P+#Ab0 - Added target_player: SELF
10. PL!-pb1-002-P+#Ab0 - Added target_player: SELF
11. PL!-pb1-003-P+#Ab0 - Added target_player: SELF
12. PL!SP-bp1-008-P#Ab0 - Added target_player: SELF
13. PL!SP-pb1-003-P+#Ab0 - Added target_player: SELF
14. PL!SP-bp4-001-P#Ab0 - Added target_player: SELF
15. PL!SP-pb1-009-P+#Ab0 - Added target_player: SELF
16. PL!N-bp1-004-P#Ab0 - Added target_player: SELF
17. PL!HS-PR-019-PR#Ab0 - Fixed is_optional and added target_player
18. PL!HS-bp1-008-P#Ab0 - Added target_player: SELF
19. PL!HS-sd1-013-SD#Ab0 - Fixed is_optional and added target_player
20. PL!HS-bp1-004-P#Ab1 - Added target_player: SELF
21. PL!HS-bp2-005-P#Ab1 - Added target_player: SELF (multiple frames)
22. PL!HS-bp1-006-P#Ab1 - Added target_player: SELF
23. PL!-bp4-005-P#Ab2 - Added target_player: SELF
24. PL!SP-bp2-010-P#Ab1 - Added target_player: SELF
25. PL!HS-bp2-021-L#Ab0 - Added target_player: SELF
26. PL!HS-bp2-023-L#Ab0 - Added target_player: SELF
27. PL!HS-bp2-025-L#Ab0 - Added target_player: SELF
28. PL!HS-PR-016-PR#Ab0 - Added JUMP_IF_FALSE
29. PL!HS-PR-017-PR#Ab0 - Added JUMP_IF_FALSE
30. PL!N-bp1-028-L#Ab0 - Added target_player: SELF
31. PL!HS-bp5-017-L#Ab0 - Added target_player: SELF
32. PL!N-bp5-028-L#Ab0 - Added target_player: SELF
33. PL!S-bp5-023-L#Ab0 - Added target_player: SELF
34. PL!HS-bp5-021-L#Ab1 - Added target_player: SELF
35. PL!HS-bp2-019-L#Ab0 - Added target_player: SELF
36. PL!SP-pb1-025-L#Ab0 - Added target_player and check_moved_this_turn
37. PL!-pb1-028-L#Ab0 - Added target_player: SELF
38. PL!-bp4-020-L#Ab0 - Added target_player: SELF
39. PL!HS-bp5-020-L#Ab0 - Added target_player: SELF
40. PL!-bp5-021-L#Ab0 - Added target_player: SELF (multiple frames)
41. PL!N-pb1-042-L#Ab0 - Added target_player: SELF
42. PL!SP-pb1-024-L#Ab0 - Added target_player: SELF
43. PL!N-bp4-031-L#Ab0 - Added target_player: SELF
44. PL!HS-bp2-026-L#Ab0 - Added target_player: SELF (multiple frames)
45. PL!SP-bp4-024-L#Ab1 - Added target_player: SELF
46. PL!-bp4-022-L#Ab0 - Added target_player: SELF
47. PL!-bp3-022-L#Ab0 - Added target_player: SELF
48. PL!N-bp1-029-L#Ab0 - Added target_player: SELF
49. PL!-pb1-029-L#Ab0 - Added target_player: SELF
50. PL!-sd1-009-SD#Ab0 - Added target_player: SELF
51. PL!S-bp2-008-P#Ab1 - Added target_player: SELF (multiple frames)
52. PL!N-bp5-016-N#Ab0 - Removed incorrect is_optional
53. PL!N-bp5-006-AR#Ab1 - Added target_player: SELF
54. PL!SP-bp4-006-P#Ab0 - Added target_player: SELF
55. PL!N-bp3-027-L#Ab0 - Added target_player: SELF
56. PL!N-bp4-025-L#Ab1 - Added target_player: SELF
57. PL!S-sd1-019-SD#Ab0 - Added target_player: SELF
58. PL!HS-bp1-023-L#Ab0 - Added target_player: SELF
59. PL!SP-bp5-023-L#Ab0 - Added target_player: SELF
60. PL!SP-bp2-025-L#Ab0 - Added target_player: SELF
61. PL!SP-bp1-024-L#Ab1 - Added target_player: SELF
62. PL!-bp4-019-L#Ab0 - Added target_player: SELF
63. PL!SP-bp5-005-AR#Ab0 - Removed incorrect is_optional
64. PL!N-PR-003-PR#Ab0 - Added target_player: SELF
65. PL!-pb1-007-P+#Ab0 - Added target_player: SELF
66. PL!-bp5-004-AR#Ab1 - Added target_player: SELF

## Verification

All changes were validated to ensure:
1. JSON remains valid
2. Frame indices remain sequential
3. No duplicate frame indices
4. All card references preserved

## Remaining Manual Fixes Required

The following abilities have identified issues but require manual review:

- **PL!-pb1-002-P+#Ab0**: "自分のステージにいるメンバーが『μ's』のみの場合" - uses GROUP_FILTER with value=4 instead of proper "only" pattern
- **PL!SP-bp4-001-P#Ab0**: 「みんなで叶える物語」ability with "のみ" condition
- **PL!-bp4-020-L#Ab0**: 「僕らのLIVE 君とのLIFE」ability with "のみ" condition

These need structural changes from GROUP_FILTER to COUNT_STAGE+SUM_VALUE pattern.
