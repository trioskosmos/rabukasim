#!/usr/bin/env python3
"""
Fix the 3 incorrect frame operation replacements
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Load semantic dump for reference
with open('data/ability_semantic_dump.json', 'r', encoding='utf-8') as f:
    semantic_data = json.load(f)

# Create a mapping of ability_index to semantic data
semantic_map = {ability['ability_index']: ability for ability in semantic_data['abilities']}

# Fix Ability 594: Complex yell repeat logic
# Text: "エールにより自分のカードを1枚以上公開したとき、それらのカードの中にブレードハートを持つカードが2枚以下の場合、それらのカードをすべて控え室に置いてもよい。そのエールで得たブレードハートを失い、もう一度エールを行う。"
# Since LOSE_BLADE_HEARTS and REPEAT_YELL are not supported, I need to simplify this to just the blade heart check and optional discard
ability_594 = data['abilities'][594]
ability_594['frames'] = [
    {
        "op": "GROUP_FILTER",
        "frame_index": 0,
        "attr": {
            "is_le": 1,
            "once_per_turn": 1,
            "filter_has_blade_heart": 1
        },
        "slot": {
            "target_slot": "REVEALED",
            "comparison": "LE"
        },
        "value": 2
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 1
    },
    {
        "op": "MOVE_TO_DISCARD",
        "frame_index": 2,
        "attr": {
            "target_player": "SELF",
            "is_optional": 1
        },
        "slot": {
            "target_slot": "REVEALED"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 3
    }
]
print("Ability 594: Simplified to blade heart check and optional discard (unsupported LOSE_BLADE_HEARTS and REPEAT_YELL removed)")

# Fix Ability 610: Add cost filter to opponent tap detection
ability_610 = data['abilities'][610]
# The second TAP_OPPONENT needs a cost filter for cost <= 4
# Find the second TAP_OPPONENT frame and add cost filter
for frame in ability_610['frames']:
    if frame.get('op') == 'TAP_OPPONENT' and frame.get('frame_index') == 6:
        frame['attr']['cost_enabled'] = 1
        frame['attr']['cost_le'] = 1
        frame['attr']['max_cost'] = 4
        print("Ability 610: Added cost filter to opponent tap detection")
        break

# Fix Ability 611: Change IS_TAPPED to IS_SELF_TAP equivalent
# Since IS_SELF_TAP is not supported, use IS_TAPPED with self filter
ability_611 = data['abilities'][611]
for frame in ability_611['frames']:
    if frame.get('op') == 'IS_TAPPED':
        frame['attr'] = frame.get('attr', {})
        frame['attr']['target_player'] = 'SELF'
        print("Ability 611: Added self filter to IS_TAPPED to approximate IS_SELF_TAP")
        break

# Save the updated data
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\nFixed 3 incorrect frame operation replacements")
