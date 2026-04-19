# Card 708 (PL!HS-bp5-017-L) Analysis

## Ability Text
ライブ開始時E支払ってもよい：自分のステージに『蓮ノ空』のメンバー1人を含むメンバーが2人以上おり、かつそれらのメンバーのユニット名がそれぞれ異なる場合、このカードのスコアを+１する。

## Ability Stages
1. Trigger: LIVE_START
2. Cost: Pay E (energy)
3. Condition: Stage has 2+ members including at least 1 Hasunosora member, AND those members have DIFFERENT unit names
4. Effect: Add +1 score

## Semantic Data (extracted)
Trigger: None (WRONG - should be LIVE_START)
Effect: 
  - Condition: member_count_at_least with group='蓮ノ空', value=2 (MISSING "different unit names" condition)
  - Action: add_score amount=1

## Issue
The semantic extraction is missing:
- The correct trigger (LIVE_START)
- The "different unit names" condition (only has member_count_at_least)

This is a semantic extraction bug, not a frame generation bug. The semantic data doesn't match the ability text.

## Test Failure
"708: matching Hasunosora unit names must not grant the score bonus even after paying the cost"
Expected: 0 (no bonus when unit names match)
Actual: 1 (bonus granted)

The condition to check for different unit names is missing, so the bonus is granted even when unit names match.
