# Card 558 Test Analysis

## Test
`test_card_558_on_play_tap_branch_only_allows_high_requirement_liella_live`

## Card
PL!SP-bp4-002-P (唐 可可)

## Ability Text (Japanese)
登場このメンバーをウェイトにしてもよい：自分のデッキの上からカードを4枚見る。その中から必 要ハートの合計が8以上の『Liella!』のライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。

## Translation
On play, may put this member in wait: look at 4 cards from top of deck. You may reveal 1 Liella! live card with total required hearts of 8 or more from among them and add to hand. Discard the rest.

## Ability Stages
1. Trigger: ON_PLAY
2. Optional cost: Put this member in wait
3. LOOK_AND_CHOOSE: Look at 4 cards from deck
4. Filter: Total required hearts >= 8, Liella group, live card
5. Select 1 Liella live card with hearts >= 8, reveal and add to hand
6. Discard remaining cards to waitroom

## Generated Frames
```
Frame 0: SET_TAPPED (optional, is_cost)
Frame 1: JUMP_IF_FALSE
Frame 2: LOOK_AND_CHOOSE, count=4, reveal=1, source_zone=DECK_TOP, target_slot=HAND, remainder_zone=DISCARD
Frame 3: RETURN
```

## Issue
**MISSING HEART TOTAL AND GROUP FILTER IN LOOK_AND_CHOOSE**

The generated frame 2 (LOOK_AND_CHOOSE) is missing:
- Heart total filter: min_hearts >= 8
- Group filter: Liella (group_id)
- Card type filter: Live card

The ability text says "必要ハートの合計が8以上の『Liella!』のライブカード" (Liella! live card with total required hearts of 8 or more), but the generated frame has no heart total or group filtering in its attr or params.

The test expects that only Liella live cards with hearts >= 8 are choosable, but the current frame allows any card to be chosen.

## Root Cause
**SEMANTIC EXTRACTION BUG**

The semantic extraction tool is not correctly parsing the "必要ハートの合計が8以上の『Liella!』のライブカード" (Liella! live card with total required hearts of 8 or more) constraint from the ability text.

## Conclusion
This is NOT a frame generation bug. The frame generation is correctly converting the (incomplete) semantic data to frames. The semantic extraction tool needs to be fixed to correctly parse the heart total and group constraint.

## Action Required
Fix semantic extraction tool to correctly handle:
- Heart total constraints in "select_from_looked_at_cards" actions
- Pattern: "必要ハートの合計がX以上の" (total required hearts X or more) should add min_hearts constraint to semantic data
