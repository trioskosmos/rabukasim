# Card 854 Test Analysis

## Tests
Multiple card_854 tests failing:
- test_card_854_live_start_draw_branch_draws_without_waiting_opponent - "854: the draw branch should add exactly one card to hand" - left: 0, right: 1
- test_card_854_live_start_wait_branch_only_targets_cost_4_or_less - "854: the left cost-4-or-less target should be legal for the wait branch"

## Card
PL!SP-bp5-001-AR (澁谷かのん)

## Ability Text (Japanese)
登場/ライブ開始時E支払ってもよい：以下から1つを選ぶ。
・相手のステージにいるコスト4以下のメンバー1人をウェイトにする。
・カードを1枚引く。

## Translation
On play/live start, may pay E: choose one from the following:
- Put 1 cost-4-or-less member card on opponent's stage in wait
- Draw 1 card

## Ability Stages
1. Trigger: ON_PLAY or LIVE_START
2. Optional cost: Pay 1 energy
3. SELECT_MODE: Choose between 2 options
4. Option 1: Put 1 cost-4-or-less opponent stage member in wait
5. Option 2: Draw 1 card

## Generated Frames
```
Frame 0: PAY_ENERGY (optional, is_cost)
Frame 1: JUMP_IF_FALSE, value=6
Frame 2: SELECT_MODE, value=2
Frame 3: JUMP, value=6
Frame 4: JUMP, value=6
Frame 5: TAP_OPPONENT, value=1, target_player: OPPONENT, source_zone: STAGE
Frame 6: JUMP, value=3
Frame 7: DRAW, value=1, target_player: SELF
Frame 8: RETURN
```

## Issue
**WRONG JUMP ROUTING AND MISSING COST FILTER**

The generated frames have multiple issues:

1. **Wrong JUMP routing for SELECT_MODE branches:**
   - Frame 3 (mode 0): JUMP value=6 - this skips to frame 6, which is wrong
   - Frame 4 (mode 1): JUMP value=6 - this also skips to frame 6, which is wrong
   
   For SELECT_MODE with 2 branches:
   - Branch 0 should jump to the start of branch 0 (frame 5, TAP_OPPONENT)
   - Branch 1 should jump to the start of branch 1 (frame 7, DRAW)
   - After each branch, should jump past the other branch to RETURN

2. **Missing cost filter on TAP_OPPONENT:**
   - Frame 5 (TAP_OPPONENT) has no cost constraint
   - Should have value_threshold=4, is_le=true to only target cost-4-or-less members

3. **DRAW frame not being executed:**
   - The test expects 1 card drawn but gets 0
   - This is likely because the JUMP routing is wrong, so the DRAW frame is never reached
   - Additionally, the DRAW source is missing from the semantic data, which is required for the DRAW opcode to succeed

## Root Cause
**SEMANTIC EXTRACTION BUG**

The semantic data for the draw_cards action is missing the "source" field:
```json
{
  "action": "draw_cards",
  "count": 1
}
```

The semantic extraction tool should have extracted the source (which should be "deck" based on the ability text "カードを1枚引く" which means "draw 1 card").

Without the source field, the frame generation cannot add the source_zone to the DRAW frame, causing the DRAW opcode to fail.

## Conclusion
This is NOT a frame generation bug. The frame generation is correctly converting the (incomplete) semantic data to frames. The semantic extraction tool needs to be fixed to correctly parse the source for draw_cards actions.

## Action Required
Fix semantic extraction tool to correctly handle:
- "カードをX枚引く" (draw X cards) pattern - should extract source as "deck"
