# Card 761 Test Analysis

## Tests
Multiple card_761 tests failing:
- test_card_761_on_play_distinct_live_names_only_enables_single_recovery_mode - "761: expected a select-mode prompt for Mia's modal recovery ability"
- test_card_761_on_play_distinct_live_groups_only_enables_double_recovery_mode - "761: expected a select-mode prompt for Mia's modal recovery ability"
- test_card_761_on_play_requires_three_distinct_lives_before_any_recovery_mode_is_legal - "761: the recovery ability should still open its modal prompt even when neither branch is legal"
- test_card_761_on_play_when_both_modes_are_legal_double_recovery_mode_stays_isolated - "761: both modes should be legal when the discard satisfies both the distinct-name and distinct-group branches"
- test_card_761_on_play_when_both_modes_are_legal_single_recovery_mode_stays_isolated - "761: the on-play recovery ability should first suspend on its modal choice" - left: None, right: Some(SelectMode)

## Card
PL!N-bp5-011-AR (ミア・テイラー)

## Ability Text (Japanese)
登場以下から1つを選ぶ。
・自分の控え室にカード名が異なるライブカードが3枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。
・自分の控え室にグループ名が異なるライブカードが3枚以上ある場合、自分の控え室からライブカードを2枚手札に加える。

## Translation
On play, choose one from the following:
- If you have 3+ live cards with different names in your discard, add 1 live card from your discard to your hand.
- If you have 3+ live cards with different group names in your discard, add 2 live cards from your discard to your hand.

## Ability Stages
1. Trigger: ON_PLAY
2. SELECT_MODE: Choose between 2 options
3. Option 1: If 3+ live cards with different names in discard, recover 1 live card
4. Option 2: If 3+ live cards with different group names in discard, recover 2 live cards

## Generated Frames
```
Frame 0: COUNT_STAGE, value=3
Frame 1: JUMP_IF_FALSE, value=1
Frame 2: SELECT_MODE, value=2
Frame 3: JUMP, value=2
Frame 4: JUMP, value=3
Frame 5: RECOVER_LIVE, value=1
Frame 6: JUMP, value=1
Frame 7: RETURN
```

## Issue
**COMPLETELY WRONG FRAMES**

The generated frames have multiple issues:

1. **Wrong condition check:**
   - Frame 0 is COUNT_STAGE checking stage for 3+ cards
   - Should check DISCARD for live cards with different names/groups
   - Should use COUNT_DISCARD with unique_names or unique_groups filter

2. **Missing second branch:**
   - Only one RECOVER_LIVE frame (value=1)
   - Missing second branch for recovering 2 cards
   - The frames only have 8 frames total, but should have more for two branches

3. **Wrong JUMP routing:**
   - Frame 3: JUMP value=2 jumps to frame 5 (RECOVER_LIVE)
   - Frame 4: JUMP value=3 jumps to frame 7 (RETURN)
   - This skips the second branch entirely

## Semantic Data
```json
{
  "condition": {
    "type": "card_count_at_least",
    "value": 3,
    "location": "waitroom",
    "card_type": "live_card",
    "different": "card_name"
  },
  "choice": true,
  "actions": [
    {
      "action": "add_to_hand",
      "count": 1,
      "card_type": "live_card"
    },
    {
      "condition": {
        "type": "card_count_at_least",
        "value": 3,
        "location": "waitroom",
        "card_type": "live_card",
        "different": "group_name"
      },
      "action": {
        "action": "add_to_hand",
        "count": 2,
        "card_type": "live_card"
      }
    }
  ]
}
```

The semantic data has:
- Top-level condition checking for 3+ distinct-name live cards in discard
- choice: true with 2 actions
- First action: add_to_hand count=1 (no condition)
- Second action: nested condition + action (3+ distinct-group live cards, then add_to_hand count=2)

The semantic data structure is unusual - the top-level condition is applied to the entire choice, but each branch should have its own condition. The frame generation is not correctly handling this structure.

## Root Cause
**SEMANTIC EXTRACTION BUG**

The semantic extraction tool is not correctly parsing the complex choice ability with:
- Top-level condition that should be per-branch conditions
- Two different conditions (different names vs different groups)
- Two different recovery amounts (1 vs 2)

The semantic data structure has a top-level condition that doesn't match the ability text structure.

## Conclusion
This is NOT a frame generation bug. The frame generation is correctly converting the (incorrect) semantic data to frames. The semantic extraction tool needs to be fixed to correctly parse the choice ability with per-branch conditions.

## Action Required
Fix semantic extraction tool to correctly handle:
- Choice abilities where each branch has its own condition
- "カード名が異なる" (different card names) pattern
- "グループ名が異なる" (different group names) pattern
- Different recovery amounts per branch
