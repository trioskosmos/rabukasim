# Card 47 Test Analysis

## Test
`test_card_47_live_start_third_mode_grants_heart06_only_to_selected_self_member`

## Card
PL!-bp3-024-L (live card)

## Ability Text (Japanese)
ライブ開始時自分の成功ライブカード置き場にカードがある場合、{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分のステージにいる『μ's』のメンバー1人は、選んだハートを1つ得る。

## Ability Stages
1. Trigger: LIVE_START
2. Condition: Success live pile has cards (count >= 1)
3. SELECT_MODE: Choose 1 from heart01, heart03, heart06
4. If heart01 selected: SELECT_MEMBER (μ's), ADD_HEARTS (heart01)
5. If heart03 selected: SELECT_MEMBER (μ's), ADD_HEARTS (heart03)
6. If heart06 selected: SELECT_MEMBER (μ's), ADD_HEARTS (heart06)

## Generated Frames
```
Frame 0: COUNT_SUCCESS_LIVE, value=1, slot={target_slot: STAGE_0, comparison: GE}
Frame 1: JUMP_IF_FALSE, value=14
Frame 2: SELECT_MODE, value=3, option_names=["選択肢1", "選択肢2", "選択肢3"]
Frame 3: JUMP, value=2 (to frame 5)
Frame 4: JUMP, value=4 (to frame 8)
Frame 5: JUMP, value=6 (to frame 11)
Frame 6: SELECT_MEMBER, value=1, attr={target_player: SELF, group_enabled: 1}, slot={target_slot: CONTEXT, source_zone: STAGE}
Frame 7: JUMP_IF_FALSE, value=1
Frame 8: ADD_HEARTS, value=1, slot={target_slot: CONTEXT}, params={heart_type: 0}  <-- WRONG: heart01
Frame 9: JUMP, value=7
Frame 10: SELECT_MEMBER, value=1, attr={target_player: SELF, group_enabled: 1}, slot={target_slot: CONTEXT, source_zone: STAGE}
Frame 11: JUMP_IF_FALSE, value=1
Frame 12: ADD_HEARTS, value=1, params={heart_type: 2}  <-- heart03
```

## Issue
**FRAME 8 HAS WRONG HEART_TYPE**

Frame 8 is the ADD_HEARTS for mode 3 (heart06 selection), but it has `heart_type: 0` (heart01) instead of `heart_type: 5` (heart06).

The frame structure is:
- Frame 3: JUMP to frame 5 (mode 1/heart01 branch)
- Frame 4: JUMP to frame 8 (mode 2/heart03 branch)
- Frame 5: JUMP to frame 11 (mode 3/heart06 branch)

But Frame 8 has heart_type: 0 (heart01) which is wrong. It should be heart_type: 2 (heart03) for mode 2.

Actually, looking more carefully:
- Frame 6-8: This is the mode 3 branch (heart06)
- Frame 8 should have heart_type: 5 (heart06) but has heart_type: 0 (heart01)

This is a frame generation bug in the semantic converter.

## Root Cause
**FRAME GENERATION BUG**

The semantic converter is not correctly mapping the mode selection to the corresponding heart type in the ADD_HEARTS frame.

## Conclusion
This IS a frame generation bug. The frame generation is not correctly setting the heart_type parameter based on the selected mode.

## Action Required
Fix semantic_to_frame_converter.py to correctly set heart_type based on mode selection.
