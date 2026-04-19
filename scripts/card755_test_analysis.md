# Card 755 Test Analysis

## Tests
Multiple card_755 tests failing:
- test_card_755_on_leaves_cost_twelve_baton_untaps_two_without_draw - "755: a cost-10+ baton target without blade hearts should untap two energy cards" - left: 2, right: 0
- test_card_755_on_leaves_cost_fifteen_baton_also_draws - "755: a cost-15 baton target without blade hearts should untap the same two energy cards" - left: 2, right: 0

## Card
PL!N-bp5-005-AR (宮下 愛)

## Ability Text (Japanese)
このメンバーがステージから控え室に置かれたとき、このメンバーがコスト10以上のブレードハートを持たない『虹ヶ咲』のメンバーとバトンタッチしていた場合、エネルギーを2枚アクティブにする。コスト15以上のブレードハートを持たない『虹ヶ咲』のメンバーの場合、さらにカードを1枚引く。

## Translation
When this member is moved from stage to waitroom, if this member baton touched with a Nijigasaki member with cost 10+ and no blade hearts, activate 2 energy cards. If the member has cost 15+ and no blade hearts, also draw 1 card.

## Ability Stages
1. Trigger: AUTO (move to waitroom)
2. Condition: Baton touch with Nijigasaki member, cost 10+, no blade hearts
3. Action: Activate 2 energy cards
4. Additional condition: If cost 15+ and no blade hearts
5. Additional action: Draw 1 card

## Generated Frames
```
Frame 0: IS_SELF_MOVE
Frame 1: JUMP_IF_FALSE, value=1
Frame 2: ACTIVATE_ENERGY, value=2
Frame 3: RETURN
```

## Issue
**COMPLETELY WRONG FRAMES**

The generated frames are missing:
1. BATON condition check (should check if baton touch with cost 10+ Nijigasaki member)
2. Cost filtering (cost 10+, cost 15+)
3. Blade heart filtering (no blade hearts)
4. Group filtering (Nijigasaki/虹ヶ咲)
5. DRAW action for cost 15+ case

## Semantic Data
```json
{
  "condition": {
    "type": "move_to_waitroom_trigger",
    "source": "stage",
    "destination": "waitroom",
    "target": "self"
  },
  "action": {
    "condition": {
      "group": "虹ヶ咲",
      "group_type": "unit",
      "card_type": "member_card",
      "cost_limit": 10,
      "type": "raw",
      "negate": true
    },
    "action": {
      "action": "activate_energy",
      "count": 2
    }
  }
}
```

The semantic data has:
- trigger condition (move_to_waitroom_trigger) - partially correct
- nested action condition with group, cost_limit, negate - but type is "raw" which is not handled
- missing: blade heart filter, baton touch condition, cost 15+ draw action

The semantic data is incomplete and has type="raw" which is not properly converted to frames.

## Root Cause
**SEMANTIC EXTRACTION BUG**

The semantic extraction tool is not correctly parsing the complex ability with:
- Baton touch condition
- Cost-based conditions (cost 10+, cost 15+)
- Blade heart filtering
- Conditional draw action based on cost

The semantic data has type="raw" which is not handled by the frame generation.

## Conclusion
This is NOT a frame generation bug. The frame generation is correctly converting the (incomplete/wrong) semantic data to frames. The semantic extraction tool needs to be fixed to correctly parse the complex ability structure.

## Action Required
Fix semantic extraction tool to correctly handle:
- Baton touch conditions
- Cost-based conditions with thresholds
- Blade heart filtering
- Conditional draw actions based on cost
- Nested conditions with multiple criteria
