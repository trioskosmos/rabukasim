# Card 697 Test Analysis

## Test
`test_card_697_live_start_discards_dollchestra_to_copy_cost_and_gain_heart`

## Card
PL!HS-bp5-005-AR (徒町 小鈴)

## Ability Text (Japanese)
ライブ開始時手札の『DOLLCHESTRA』のカードを1枚控え室に置いてもよい：自分のステージにいる『DOLLCHESTRA』のメンバー1人を選ぶ。ライブ終了時まで、このメンバーのコストは、選んだメンバーが元々持つコストより1低い値に等しくなる。これによりこのカードのコストが10以上になった場合、ライブ終了時まで、{{heart_05.png|heart05}}を得る。

## Translation
At live start, may discard 1 DOLLCHESTRA card from hand: select 1 DOLLCHESTRA member on stage. Until end of live, this member's cost equals 1 lower than the selected member's original cost. If this card's cost becomes 10 or higher through this, gain heart05 until end of live.

## Ability Stages
1. Trigger: LIVE_START
2. Optional cost: Discard 1 DOLLCHESTRA card from hand
3. Select 1 DOLLCHESTRA member on stage
4. Set this member's cost to (selected member's cost - 1) until end of live
5. If cost >= 10, gain heart05 until end of live

## Generated Frames
```
Frame 0: MOVE_TO_DISCARD (optional, from HAND to DISCARD, target_slot: STAGE_1)
Frame 1: JUMP_IF_FALSE
Frame 2: ADD_HEARTS (heart05)
Frame 3: RETURN
```

## Issue
**COMPLETELY WRONG FRAMES**

The generated frames are:
1. MOVE_TO_DISCARD from hand (correct as optional cost)
2. JUMP_IF_FALSE (correct)
3. ADD_HEARTS heart05 (wrong - this should only happen if cost >= 10)
4. RETURN (correct)

Missing:
- SELECT_MEMBER to select DOLLCHESTRA member on stage
- SYNC_COST or SET_COST to set cost to (selected member's cost - 1)
- Conditional check for cost >= 10 before granting heart05

## Semantic Data
The semantic extraction tool is not correctly parsing the ability text. It's missing:
- The select member action
- The cost copy/modify action
- The conditional heart gain

## Root Cause
**SEMANTIC EXTRACTION BUG**

The semantic extraction tool is not correctly parsing the complex ability text with cost modification and conditional effects.

## Conclusion
This is NOT a frame generation bug. The frame generation is correctly converting the (incorrect) semantic data to frames. The semantic extraction tool needs to be fixed to correctly parse the ability text.

## Action Required
Fix semantic extraction tool to correctly handle:
- Optional discard costs followed by selection
- Cost modification based on selected member's cost
- Conditional effects based on modified cost
