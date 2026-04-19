# Frame Comparison Analysis: Authored vs Converted

## Test Results
- **Total tests**: 693
- **Passed**: 603
- **Failed**: 90
- **Ignored**: 7

## Mismatched Cards by Pattern

### 1. surplus_heart (余剰ハートを持たない場合)
**Pattern**: "余剰ハートを持たない場合" (When having no surplus hearts)

**Cards**:
- PL!-bp3-025-L (タカラモノズ)
- PL!N-bp5-010-R (三船栞子)
- PL!N-bp5-010-AR (三船栞子)

**Issues**:
- Frame count mismatch: Authored 7 vs Converted 6
- OP mismatches:
  - COUNT_HEARTS vs HAS_EXCESS_HEART
  - BOOST_SCORE vs COUNT_HEARTS
  - COUNT_HEARTS vs JUMP_IF_FALSE
  - JUMP_IF_FALSE vs SET_SCORE

**Root Cause**: Converter uses HAS_EXCESS_HEART instead of COUNT_HEARTS for checking surplus heart conditions.

### 2. names_different (名前が異なる場合)
**Pattern**: "名前が異なる場合" (When names are different)

**Cards**:
- PL!HS-bp1-003-R+ (乙宗 梢)
- PL!HS-bp1-003-P (乙宗 梢)
- PL!HS-bp1-003-P+ (乙宗 梢)

**Issues**:
- Frame count mismatch: Authored 4 vs Converted 3
- OP mismatches:
  - COUNT_STAGE vs AREA_CHECK
  - SUM_VALUE vs PAY_ENERGY
  - PAY_ENERGY vs RECOVER_MEMBER
  - RECOVER_MEMBER vs RETURN

**Root Cause**: Converter uses AREA_CHECK instead of COUNT_STAGE for name differentiation checks.

### 3. opponent_member_to_wait (相手のステージにいるコスト4以下のメンバー1人をウェイトにする)
**Pattern**: "相手のステージにいるコスト4以下のメンバー1人をウェイトにする" (Tap 1 opponent member with cost 4 or less on stage)

**Cards**:
- PL!-PR-007-PR (東條 希)
- PL!-PR-009-PR (矢澤にこ)
- PL!S-bp3-012-N (松浦果南)

**Issues**:
- Ability count mismatches
- OP mismatches:
  - SELECT_MEMBER vs TAP_OPPONENT
  - MOVE_MEMBER vs RETURN

**Root Cause**: Converter uses TAP_OPPONENT instead of SELECT_MEMBER + MOVE_MEMBER for opponent tap effects.

**Related failing test**: test_q168_q169_q170_q181_q188_nico_exhaustive (矢澤にこ)

### 4. waitroom_live_recovery (自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える)
**Pattern**: "自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える" (Add 1 Nijigasaki live card from waitroom to hand)

**Cards**:
- PL!N-bp1-003-R+ (桜坂しずく)
- PL!N-bp1-003-P (桜坂しずく)
- PL!N-bp1-003-P+ (桜坂しずく)

**Issues**:
- Frame count mismatches: Authored 6 vs Converted 4, Authored 4 vs Converted 5
- OP mismatches:
  - BATON vs MOVE_TO_DISCARD
  - COUNT_ENERGY vs RECOVER_LIVE
  - JUMP_IF_FALSE vs RETURN
  - MOVE_TO_DISCARD vs PAY_ENERGY
  - LOOK_AND_CHOOSE vs META_RULE
  - RETURN vs ADD_HEARTS

**Root Cause**: Converter incorrectly handles baton touch + live recovery combinations.

## Summary of Issues

The semantic-to-frame converter has systematic differences from authored frames:

1. **Heart counting**: Uses HAS_EXCESS_HEART instead of COUNT_HEARTS for surplus checks
2. **Stage operations**: Uses AREA_CHECK instead of COUNT_STAGE for name differentiation
3. **Opponent targeting**: Uses TAP_OPPONENT instead of SELECT_MEMBER + MOVE_MEMBER
4. **Baton/recovery**: Incorrectly sequences BATON, MOVE_TO_DISCARD, and RECOVER_LIVE operations

## Next Steps

1. Fix semantic_to_frame_converter.py for each pattern
2. Regenerate frames
3. Recompile cards
4. Run tests to verify fixes
