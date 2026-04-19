# Card 777 Test Analysis

## Test
`test_card_777_live_start_selected_kasumi_colors_grant_matching_hearts`

## Card
PL!N-bp5-029-L (live card)

## Ability Text (Japanese)
ライブ開始時自分のステージに「中須かすみ」がいる場合、自分のデッキの上からカードを4枚公開する。自分はそれらの中から「中須かすみ」のカードを1枚選ぶ。ライブ終了時まで、自分のステージにいる「中須かすみ」1人は、これにより選んだカードが持つ色のハートを1つずつ得る。公開したカードをすべて控え室に置く。

## Ability Stages
1. Trigger: LIVE_START
2. Condition: Kasumi (中須かすみ) present on stage
3. Reveal 4 cards from top of deck
4. Select 1 Kasumi card from revealed cards
5. Grant hearts based on selected card's colors to Kasumi on stage (until end of live)
6. Discard all revealed cards to waitroom

## Generated Frames
```
Frame 0: HAS_KEYWORD, value=0, attr={target_player: SELF}, slot={target_slot: CONTEXT, comparison: GE}
Frame 1: JUMP_IF_FALSE, value=1
Frame 2: MOVE_TO_DISCARD, value=1, attr={target_player: SELF, zone_mask: Guest+Friend}, slot={source_zone: STAGE, dest_zone: DISCARD, target_slot: CONTEXT}
Frame 3: RETURN
```

## Issue
**COMPLETELY WRONG FRAMES**

The generated frames are:
1. HAS_KEYWORD (checking if Kasumi is on stage) - wrong opcode, should be character check
2. JUMP_IF_FALSE - correct
3. MOVE_TO_DISCARD from stage to discard - wrong, should be REVEAL_CARDS from deck
4. RETURN - correct

Missing:
- REVEAL_CARDS to reveal 4 cards from deck
- SELECT_CARDS or SELECT_MEMBER to select 1 Kasumi card
- ADD_HEARTS to grant hearts based on colors
- MOVE_TO_DISCARD to discard revealed cards

## Semantic Data
Trigger: None (WRONG - should be LIVE_START)
Effect:
- Condition: character_presence (Kasumi on stage) - CORRECT
- Actions: [{count: 4, duration: until_end_of_live}, {discard_to_waitroom from stage}] - COMPLETELY WRONG

## Root Cause
**SEMANTIC EXTRACTION BUG**

The semantic extraction tool is not correctly parsing the ability text. It's missing:
- The reveal action
- The select action
- The grant hearts action
- The correct discard action (should discard revealed cards, not stage cards)

## Conclusion
This is NOT a frame generation bug. The frame generation is correctly converting the (incorrect) semantic data to frames. The semantic extraction tool needs to be fixed to correctly parse the ability text.

## Action Required
Fix semantic extraction tool to correctly handle:
- Reveal cards from deck actions
- Select card from revealed cards actions
- Grant hearts based on selected card's colors actions
- Discard revealed cards actions
