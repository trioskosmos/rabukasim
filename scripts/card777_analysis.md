# Card 777 Analysis

## Ability Text (Japanese)
ライブ開始時自分のステージに「中須かすみ」がいる場合、自分のデッキの上からカードを4枚公開する。自分はそれらの中から「中須かすみ」のカードを1枚選ぶ。ライブ終了時まで、自分のステージにいる「中須かすみ」1人は、これにより選んだカードが持つ色のハートを1つずつ得る。公開したカードをすべて控え室に置く。

## Ability Stages
1. Trigger: LIVE_START
2. Condition: Kasumi (中須かすみ) present on stage
3. Reveal 4 cards from top of deck
4. Select 1 Kasumi card from revealed cards
5. Grant hearts based on selected card's colors to Kasumi on stage (until end of live)
6. Discard all revealed cards to waitroom

## Semantic Data (extracted)
Trigger: None (CONSTANT - WRONG)
Effect: 
  - Condition: character_presence (Kasumi on stage) - CORRECT
  - Actions: 
    - count: 4, duration: until_end_of_live (INCOMPLETE - missing reveal)
    - discard_to_waitroom from stage (WRONG - should be discard revealed cards)

## Current Generated Frames
Ability 0:
  0: HAS_KEYWORD value=0
  1: JUMP_IF_FALSE value=1
  2: MOVE_TO_DISCARD value=1
  3: RETURN value=None

## Issue
The semantic extraction is completely wrong for this ability. It's missing:
- The reveal 4 cards from deck action
- The select 1 Kasumi card from revealed action
- The grant hearts based on colors action
- The correct discard action (should discard revealed cards, not stage cards)

This is a semantic extraction bug, not a frame generation bug. The semantic data doesn't match the ability text at all.
