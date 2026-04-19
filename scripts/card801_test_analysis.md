# Card 801 Test Analysis

## Test
`test_card_801_on_play_only_high_cost_aqours_choice_is_legal_and_remainders_discard`

## Card
PL!S-bp5-006-AR (津島善子)

## Ability Text (Japanese)
登場このメンバーをウェイトにし、手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からコスト9以上の『Aqours』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。

## Translation
On play, put this member in wait and may discard 1 card from hand: look at 5 cards from top of deck. You may reveal 1 Aqours member card with cost 9 or more from among them and add to hand. Discard the rest.

## Ability Stages
1. Trigger: ON_PLAY
2. Cost: Put this member in wait, may discard 1 card from hand
3. LOOK_AND_CHOOSE: Look at 5 cards from deck
4. Filter: Cost >= 9, Aqours group
5. Select 1 Aqours member card with cost >= 9, reveal and add to hand
6. Discard remaining cards to waitroom

## Generated Frames
```
Frame 0: MOVE_TO_DISCARD (optional, from HAND to DISCARD, target_slot: STAGE_1)
Frame 1: JUMP_IF_FALSE
Frame 2: LOOK_AND_CHOOSE, count=5, reveal=1, source_zone=DECK_TOP, target_slot=HAND, remainder_zone=DISCARD
Frame 3: RETURN
```

## Issue
**MISSING COST AND GROUP FILTER IN LOOK_AND_CHOOSE**

The generated frame 2 (LOOK_AND_CHOOSE) is missing:
- Cost filter: min_cost >= 9
- Group filter: Aqours (group_id)

The ability text says "コスト9以上の『Aqours』のメンバーカード" (Aqours member card with cost 9 or more), but the generated frame has no cost or group filtering in its attr.

The test expects that only Aqours members with cost >= 9 are choosable, but the current frame allows any card to be chosen.

## Semantic Data
```json
{
  "action": "select_from_looked_at_cards",
  "count": 1,
  "destination": "hand",
  "remainder_zone": "DISCARD",
  "group": "Aqours",
  "group_type": "unit",
  "card_type": "member_card"
}
```

The semantic data has:
- group: "Aqours" ✓
- group_type: "unit" ✓
- card_type: "member_card" ✓
- **MISSING: cost constraint (>= 9)**

## Root Cause
**SEMANTIC EXTRACTION BUG**

The semantic extraction tool is not correctly parsing the "コスト9以上の" (cost 9 or more) constraint from the ability text. It's extracting the group and card type, but not the cost constraint.

## Conclusion
This is NOT a frame generation bug. The frame generation is correctly converting the (incomplete) semantic data to frames. The semantic extraction tool needs to be fixed to correctly parse the cost constraint.

## Action Required
Fix semantic extraction tool to correctly handle:
- Cost constraints in "select_from_looked_at_cards" actions
- Pattern: "コストX以上の" (cost X or more) should add min_cost constraint to semantic data
