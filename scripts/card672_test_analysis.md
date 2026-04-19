# Card 672 Test Analysis

## Tests
Multiple card_672 tests failing:
- test_card_672_private_wars_first_mode_activates_waiting_member_and_adds_blade - "672: the waiting ally should be targetable for the first mode"
- test_card_672_private_wars_second_mode_only_targets_opponent_with_three_or_less_blades - "672: the low-blade opponent should become waiting"

## Card
PL!-bp5-024-L (Private Wars) - Live Card

## Ability Text (Japanese)
ライブ開始時自分のステージに『A-RISE』のメンバーがいる場合、以下から1つを選ぶ。
・ウェイト状態のメンバー1人をアクティブにし、ライブ終了時まで、そのメンバーはブレードを得る。
・相手のステージにいる元々持つブレードが3つ以下のメンバー1人をウェイトにする。

## Translation
On live start, if you have an A-RISE member on your stage, choose one from the following:
- Activate 1 waiting member and give it blades until end of live.
- Send 1 opponent member with 3 or fewer original blades to wait.

## Ability Stages
1. Trigger: LIVE_START
2. Condition: A-RISE member on stage
3. SELECT_MODE: Choose between 2 options
4. Option 1: Activate waiting member + give blades until end of live
5. Option 2: Send opponent member with <=3 original blades to wait

## Generated Frames
```
Frame 0: COUNT_STAGE, group_id="ARISE"
Frame 1: JUMP_IF_FALSE, value=1
Frame 2: SELECT_MODE, value=2
Frame 3: JUMP, value=2
Frame 4: JUMP, value=3
Frame 5: ACTIVATE_MEMBER, value=1
Frame 6: JUMP, value=2
Frame 7: TAP_OPPONENT, value=1, params: filter="BLADE_LE2"
Frame 8: RETURN
```

## Issue
**FRAME GENERATION BUG**

The generated frames have multiple issues:

1. **Missing is_tapped filter on ACTIVATE_MEMBER:**
   - Frame 5 (ACTIVATE_MEMBER) doesn't have is_tapped=1 to only target waiting members
   - Should only target members in wait state (source_state="wait" in semantic data)

2. **Missing ADD_BLADES frame:**
   - No frame to add blades after ACTIVATE_MEMBER
   - Semantic data has gain_resource action with resource="blade" and duration="until_end_of_live"

3. **Wrong blade count filter:**
   - Frame 7 has filter="BLADE_LE2" (<= 2 blades)
   - Should be filter="BLADE_LE3" (<= 3 blades) based on semantic data: original_blade_count=3, original_blade_operator="<="

## Semantic Data
```json
{
  "condition": {
    "group": "A-RISE",
    "group_type": "unit",
    "type": "member_presence"
  },
  "choice": true,
  "actions": [
    {
      "actions": [
        {
          "action": "activate_member",
          "source_state": "wait"
        },
        {
          "resource": "blade",
          "actions": [
            {
              "duration": "until_end_of_live"
            },
            {
              "action": "gain_resource",
              "resource": "blade",
              "blade_count": 1
            }
          ]
        }
      ]
    },
    {
      "action": "member_to_wait",
      "original_blade_count": 3,
      "original_blade_operator": "<="
    }
  ]
}
```

The semantic data is correct:
- source_state="wait" for activate_member
- gain_resource with resource="blade" and duration="until_end_of_live"
- original_blade_count=3, original_blade_operator="<=" for member_to_wait

## Root Cause
**FRAME GENERATION BUG**

The semantic_to_frame_converter is not:
1. Adding is_tapped filter when source_state="wait" for activate_member
2. Generating ADD_BLADES frame for gain_resource action with resource="blade"
3. Using correct blade count filter (BLADE_LE3 instead of BLADE_LE2) for original_blade_count=3

## Conclusion
This IS a frame generation bug. The semantic data is correct, but the frame generation is missing filters and frames.

## Action Required
Fix semantic_to_frame_converter.py to:
1. Add is_tapped=1 filter to ACTIVATE_MEMBER when source_state="wait"
2. Generate ADD_BLADES frame for gain_resource action with resource="blade" and duration="until_end_of_live"
3. Fix blade count filter mapping to use correct threshold (3 instead of 2)
