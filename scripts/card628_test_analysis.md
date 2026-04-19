# Card 628 Test Analysis

## Test
`test_card_628_live_start_prompts_optional_topdeck_discard`

## Card
PL!SP-bp5-009-AR (鬼塚夏美) - card_id 862

## Ability Text (Japanese)
ライブ開始時自分のデッキの一番上のカードを控え室に置いてもよい。そうした場合、ライブ終了時まで、ブレードを得る。これにより控え室に置いたカードがライブカードの場合、このメンバーをウェイトにする。自分はこの手順をさらに4回まで繰り返してもよい。

## Translation
At live start, may discard the top card of your deck. If you do, gain blades until end of live. If the discarded card is a live card, put this member in wait. You may repeat this procedure up to 4 more times.

## Ability Stages
1. Trigger: LIVE_START
2. Optional: Discard top card of deck
3. If discarded, gain blades until end of live
4. If discarded card is live card, put this member in wait
5. Repeat up to 4 more times (total 5 times)

## Generated Frames
```
Frame 0: SET_TAPPED
Frame 1: RETURN
```

## Issue
**COMPLETELY WRONG FRAMES**

The generated frames are:
1. SET_TAPPED - wrong, should be discard from deck
2. RETURN - correct

Missing:
- Optional discard from deck top
- Check if live card was discarded
- ADD_BLADES if yes
- PUT_TO_WAIT if live card
- Repeat up to 4 more times

## Root Cause
**SEMANTIC EXTRACTION BUG**

The semantic extraction tool is not correctly parsing the complex ability text with:
- Optional discard
- Conditional effects based on what was discarded
- Repeatable action (up to 4 more times)

## Conclusion
This is NOT a frame generation bug. The frame generation is correctly converting the (incorrect) semantic data to frames. The semantic extraction tool needs to be fixed to correctly parse the complex ability structure.

## Action Required
Fix semantic extraction tool to correctly handle:
- Optional discard actions
- Conditional effects based on discarded card type
- Repeatable actions with "up to X more times" (さらにX回まで繰り返してもよい)
