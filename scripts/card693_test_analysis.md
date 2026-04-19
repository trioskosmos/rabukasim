# Card 693 Test Analysis

## Tests
Multiple card_693 tests failing:
- test_card_693_on_play_mills_four_without_blade_bonus_when_no_live_is_milled
- test_card_693_on_play_mills_four_and_gains_blades_when_a_live_is_milled
- test_card_693_reveal_three_blade_heart_types_adds_heart01_only
- test_card_693_reveal_six_blade_heart_types_adds_heart01_and_grants_score

## Card
PL!HS-bp5-001-AR (日野下花帆)

## Ability Text (Japanese) - Ability 0
登場自分のデッキの上からカードを4枚控え室に置く。それらの中にライブカードがある場合、ライブ終了時まで、ブレードブレードを得る。

## Translation
On play, mill 4 cards from top of deck to discard. If there's a live card among them, gain 2 blades until end of live.

## Ability Stages
1. Trigger: ON_PLAY
2. Mill 4 cards from deck to discard
3. Check if live card is among milled cards
4. If yes, gain 2 blades until end of live

## Generated Frames
```
Frame 0: HAS_MEMBER (checking if member exists)
Frame 1: JUMP_IF_FALSE
Frame 2: ADD_BLADES
Frame 3: RETURN
```

## Issue
**COMPLETELY WRONG FRAMES**

The generated frames are:
1. HAS_MEMBER (checking if member exists) - wrong, should be mill action
2. JUMP_IF_FALSE - correct
3. ADD_BLADES - wrong, should be conditional on live card in milled cards
4. RETURN - correct

Missing:
- MOVE_TO_DISCARD to mill 4 cards from deck
- COUNT or check for live card in discard
- Conditional ADD_BLADES only if live card was in milled cards

## Root Cause
**SEMANTIC EXTRACTION BUG**

The semantic extraction tool is not correctly parsing the ability text. It's missing:
- The mill action
- The conditional check for live card in milled cards

## Conclusion
This is NOT a frame generation bug. The frame generation is correctly converting the (incorrect) semantic data to frames. The semantic extraction tool needs to be fixed to correctly parse the ability text.

## Action Required
Fix semantic extraction tool to correctly handle:
- Mill actions (move cards from deck to discard)
- Conditional effects based on what was milled
