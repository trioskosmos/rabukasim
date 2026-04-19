# Card 656 Test Analysis

## Tests
Multiple card_656 tests failing:
- test_card_656_on_play_baton_discard_down_then_draw_three_for_both_players
- test_card_656_on_play_response_hands_off_from_controller_to_opponent_and_back

## Card
PL!-bp5-007-AR (東條 希)

## Ability Text (Japanese)
登場このメンバーよりコストが低いメンバーからバトンタッチして登場した場合、自分と相手はそれぞれ自身の手札の枚数が3枚になるまで手札を控え室に置き、その後、自分と相手はそれぞれカードを3枚引く。

## Translation
On play, if you baton touch from a member with lower cost than this member, you and your opponent each discard from your hand until you have 3 cards in hand, then you and your opponent each draw 3 cards.

## Ability Stages
1. Trigger: ON_PLAY
2. Condition: Baton touch from member with lower cost
3. Discard hand until 3 cards (both players)
4. Draw 3 cards (both players)

## Generated Frames
```
Frame 0: BATON, target_player: SELF
Frame 1: JUMP_IF_FALSE, value=1
Frame 2: DRAW, value=3, target_player: SELF
Frame 3: RETURN
```

## Issue
**MISSING DISCARD ACTION AND BOTH PLAYERS ASPECT**

The generated frames are missing:
- Discard hand until 3 cards
- Apply effect to both players (not just self)
- Source should be deck (not waitroom as in semantic data)

The ability text says "自分と相手はそれぞれ自身の手札の枚数が3枚になるまで手札を控え室に置き、その後、自分と相手はそれぞれカードを3枚引く" (you and your opponent each discard until 3 cards, then you and your opponent each draw 3 cards), but the generated frame only has DRAW for self.

## Semantic Data
```json
{
  "condition": {
    "type": "baton_touch_deploy",
    "cost_comparison": "lower"
  },
  "action": {
    "action": "draw_cards",
    "count": 3,
    "source": "waitroom"
  }
}
```

The semantic data has:
- action: "draw_cards" (wrong - should include discard first)
- source: "waitroom" (wrong - should be deck)
- Missing: discard to 3 action
- Missing: both players aspect

## Root Cause
**SEMANTIC EXTRACTION BUG**

The semantic extraction tool is not correctly parsing the complex ability text with both discard and draw actions affecting both players.

## Conclusion
This is NOT a frame generation bug. The frame generation is correctly converting the (incomplete) semantic data to frames. The semantic extraction tool needs to be fixed to correctly parse the discard-to-3 and draw-3 actions affecting both players.

## Action Required
Fix semantic extraction tool to correctly handle:
- Complex abilities with multiple sequential actions (discard then draw)
- "Both players" (自分と相手) targeting
- "Discard until X cards" (手札の枚数がX枚になるまで手札を控え室に置く) pattern
