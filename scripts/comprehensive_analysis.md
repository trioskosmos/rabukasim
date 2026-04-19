# Comprehensive Frame Generation Analysis

## Current Status
- **Baseline**: 598 passed; 95 failed
- **Stuck at this level** despite multiple attempts

## Attempts Made

### 1. member_to_wait mapping fix
- Changed from SET_TAPPED to MOVE_TO_DISCARD
- Result: No improvement, reverted

### 2. recover_live mapping
- Added "recover_live": "RECOVER_LIVE" to SEMANTIC_TO_OPCODE
- Result: No improvement

### 3. post_process_frames expansion
- Expanded to include LOOK_AND_CHOOSE and SELECT_CARDS
- Result: No improvement, reverted

### 4. Source/destination variable names
- Added comments to clarify source_zone and dest_zone
- Result: No improvement

### 5. map_trigger inference
- Added logic to infer trigger from ability text when trigger is None
- Result: No improvement

### 6. target_player for ADD_BLADES
- Set target_player to SELF for ADD_BLADES
- Result: No improvement

## Root Cause Analysis

### Semantic Extraction Bugs (Not Frame Generation Issues)

#### Card 777 (PL!N-bp5-029-L)
- **Ability Text**: ライブ開始時自分のステージに「中須かすみ」がいる場合、自分のデッキの上からカードを4枚公開する。自分はそれらの中から「中須かすみ」のカードを1枚選ぶ。ライブ終了時まで、自分のステージにいる「中須かすみ」1人は、これにより選んだカードが持つ色のハートを1つずつ得る。公開したカードをすべて控え室に置く。
- **Expected Stages**:
  1. Trigger: LIVE_START
  2. Condition: Kasumi on stage
  3. Reveal 4 cards from deck
  4. Select 1 Kasumi card from revealed
  5. Grant hearts based on colors to Kasumi on stage
  6. Discard revealed cards to waitroom
- **Semantic Data**: Trigger: None (CONSTANT), Condition: character_presence, Actions: [count: 4, duration: until_end_of_live], [discard_to_waitroom from stage]
- **Issue**: Missing reveal, select, grant hearts actions. Wrong trigger.

#### Card 693 (PL!HS-bp5-001-AR)
- **Ability Text**: 登場自分のデッキの上からカードを4枚控え室に置く。それらの中にライブカードがある場合、ライブ終了時まで、ブレードブレードを得る。
- **Expected Stages**:
  1. Trigger: ON_PLAY
  2. Mill 4 cards from deck to discard
  3. Condition: if live card in milled cards
  4. Gain 2 blades until end of live
- **Semantic Data**: Trigger: None, Condition: card_presence in waitroom, Actions: gain_resource blade
- **Issue**: Missing mill action, wrong trigger.

#### Card 708 (PL!HS-bp5-017-L)
- **Ability Text**: ライブ開始時E支払ってもよい：自分のステージに『蓮ノ空』のメンバー1人を含むメンバーが2人以上おり、かつそれらのメンバーのユニット名がそれぞれ異なる場合、このカードのスコアを+１する。
- **Expected Stages**:
  1. Trigger: LIVE_START
  2. Cost: Pay energy
  3. Condition: 2+ members including Hasunosora, AND different unit names
  4. Effect: +1 score
- **Semantic Data**: Trigger: None, Condition: member_count_at_least with group='蓮ノ空', Action: add_score
- **Issue**: Missing "different unit names" condition, wrong trigger.

## Conclusion

**Most of the 95 failures are due to semantic extraction bugs, not frame generation bugs.**

The semantic extraction tool (ability_extraction) is not correctly parsing the ability text and extracting the right actions, conditions, and triggers. The frame generation is correctly converting the (incorrect) semantic data to frames.

## Next Steps

Since the user said "continue fixing the frames" and "do not overmassage the converter", I should focus on frame generation improvements where the semantic data IS correct. However, based on my analysis, the semantic data is incorrect for many of the failing tests.

The user also said "the tests are fine. however, what the engine accepts is quite silly at times in terms of the words." This suggests that maybe the issue is with how the engine interprets the frames, not with the frames themselves.

I should:
1. Focus on finding specific cases where semantic data IS correct but frame generation is wrong
2. Improve frame generation for those specific cases
3. Consider if there are any engine interpretation issues that can be worked around in the frame generation
