# Card 709 Test Analysis

## Test
`test_live_709_live_start_with_duplicate_cost_skips_score_bonus`

## Card
PL!HS-bp5-018-L (AURORA FLOWER)

## Ability Text (Japanese)
ライブ開始時自分のステージに名前とコストが両方ともそれぞれ異なるメンバーが3人以上いる場合、このカードのスコアを+１する。

## Translation
At live start, if there are 3+ members on stage with BOTH different names AND different costs, this card's score +1.

## Ability Stages
1. Trigger: LIVE_START
2. Condition: 3+ members on stage with unique names AND unique costs
3. Effect: BOOST_SCORE +1

## Generated Frames
```
Frame 0: COUNT_STAGE, value=3, attr={target_player: SELF, unique_names: 1}, slot={target_slot: STAGE_0, comparison: GE}
Frame 1: JUMP_IF_FALSE, value=1
Frame 2: BOOST_SCORE, value=1, attr={target_player: SELF}, slot={target_slot: CONTEXT}
Frame 3: RETURN
```

## Issue
**MISSING "UNIQUE COSTS" CONDITION**

The generated frame only checks `unique_names: 1` but doesn't check for unique costs. The ability text says "名前とコストが両方ともそれぞれ異なる" (both names and costs are respectively different), meaning we need to check that BOTH names are unique AND costs are unique.

The test sets up 3 members with duplicate costs but distinct names. It expects live_score_bonus = 0 (no bonus) because the costs are not all different. But the generated frame only checks unique_names, so it grants the bonus.

## Semantic Data
The semantic extraction tool needs to extract both:
- "unique_names" condition
- "unique_costs" condition

Currently it only extracts the "unique_names" condition.

## Root Cause
**SEMANTIC EXTRACTION BUG**

The semantic extraction tool is not correctly parsing the "名前とコストが両方ともそれぞれ異なる" (both names and costs are respectively different) condition. It's missing the "unique costs" condition.

## Conclusion
This is NOT a frame generation bug. The frame generation is correctly converting the (incomplete) semantic data to frames. The semantic extraction tool needs to be fixed to correctly parse the "different costs" condition.

## Action Required
Fix semantic extraction tool to correctly handle:
- "名前とコストが両方ともそれぞれ異なる" → both unique_names and unique_costs conditions
