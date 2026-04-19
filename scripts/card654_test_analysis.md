# Card 654 Test Analysis

## Test
`test_card_654_on_play_score_six_success_pile_adds_energy`

## Card
PL!-bp5-005-AR (星空凛)

## Ability Text (Japanese)
登場自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、自分のエネルギーデッキから、エネルギーカードを1枚アクティブ状態で置く。

## Translation
On play, if the total score of cards in success live pile is 6 or more, place 1 energy card from energy deck in active state.

## Ability Stages
1. Trigger: ON_PLAY
2. Condition: Total score of success live pile >= 6
3. Draw 1 energy card from energy deck in active state

## Generated Frames
```
Frame 0: SCORE_TOTAL_CHECK, value=6, attr={target_player: SELF}, slot={target_slot: CONTEXT, comparison: GE}
Frame 1: JUMP_IF_FALSE, value=1
Frame 2: MOVE_TO_DISCARD, value=1, attr={target_player: SELF}, slot={source_zone: "", dest_zone: DISCARD, target_slot: CONTEXT}
Frame 3: RETURN
```

## Issue
**WRONG OPCODE AND EMPTY SOURCE_ZONE**

The generated frame 2 is:
- MOVE_TO_DISCARD (wrong - should be DRAW_ENERGY or similar)
- source_zone: "" (empty - wrong, should be ENERGY)
- dest_zone: DISCARD (wrong - should be ENERGY_ZONE)

The ability text says "自分のエネルギーデッキから、エネルギーカードを1枚アクティブ状態で置く" (place 1 energy card from energy deck in active state), but the generated frame is trying to move to discard from an empty source zone.

## Root Cause
**FRAME GENERATION BUG**

The semantic_to_frame_converter is not correctly mapping the action "place 1 energy card from energy deck in active state" to the correct frame. It's generating MOVE_TO_DISCARD instead of DRAW_ENERGY, and the source_zone is empty.

## Conclusion
This IS a frame generation bug. The semantic data likely has the correct action, but the frame generation is not correctly converting it to the right opcode and zone mapping.

## Action Required
Fix semantic_to_frame_converter.py to correctly handle:
- Drawing energy cards from energy deck
- Setting source_zone to ENERGY
- Setting dest_zone to ENERGY_ZONE (not DISCARD)
- Using correct opcode (DRAW_ENERGY or similar, not MOVE_TO_DISCARD)
