#!/usr/bin/env python3
"""
Fix abilities with missing jumps (JUMP_IF_FALSE at frame 0 without preceding condition)
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

# Fix ability 446: Add condition for energy under member
ability_446 = data['abilities'][446]
ability_446['frames'] = [
    {
        "op": "COUNT_ENERGY",
        "frame_index": 0,
        "value": 2,
        "attr": {
            "is_le": 0
        },
        "slot": {
            "target_slot": "UNDER_MEMBER",
            "comparison": "GE"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 1
    },
    {
        "op": "BOOST_SCORE",
        "frame_index": 2,
        "value": 1,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 3
    }
]
print("Ability 446: Added COUNT_ENERGY condition")

# Fix ability 468: Add condition for center cost check
ability_468 = data['abilities'][468]
ability_468['frames'] = [
    {
        "op": "COST_CHECK",
        "frame_index": 0,
        "attr": {
            "is_center": 1,
            "is_highest": 1
        },
        "slot": {
            "target_slot": "STAGE",
            "comparison": "GE"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 1
    },
    {
        "op": "ADD_HEARTS",
        "frame_index": 2,
        "value": 1,
        "slot": {
            "target_slot": "CONTEXT"
        },
        "params": {
            "heart_type": 3
        }
    },
    {
        "op": "RETURN",
        "frame_index": 3
    }
]
print("Ability 468: Added COST_CHECK condition")

# Fix ability 492: Add condition for success pile check
ability_492 = data['abilities'][492]
ability_492['frames'] = [
    {
        "op": "IS_IN_DISCARD",
        "frame_index": 0,
        "attr": {
            "zone": "SUCCESS_PILE"
        },
        "slot": {
            "target_slot": "CONTEXT",
            "comparison": "GE"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 3
    },
    {
        "op": "COUNT_STAGE",
        "frame_index": 2,
        "attr": {
            "group_enabled": 1,
            "group_id": "MUSE"
        },
        "slot": {
            "target_slot": "STAGE_CENTER",
            "comparison": "GE"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 3,
        "value": 1
    },
    {
        "op": "ADD_BLADES",
        "frame_index": 4,
        "value": 1,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 5
    }
]
print("Ability 492: Added IS_IN_DISCARD condition")

# Fix ability 595: Add condition for self move or energy placement
ability_595 = data['abilities'][595]
ability_595['frames'] = [
    {
        "op": "IS_SELF_MOVE",
        "frame_index": 0,
        "attr": {
            "once_per_turn": 1
        },
        "slot": {
            "target_slot": "STAGE_0",
            "comparison": "GE"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 2
    },
    {
        "op": "DRAW",
        "frame_index": 2,
        "value": 1,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "ADD_HEARTS",
        "frame_index": 3,
        "value": 1,
        "attr": {
            "target_player": "SELF"
        },
        "slot": {
            "target_slot": "CONTEXT"
        },
        "params": {
            "heart_type": 2
        }
    },
    {
        "op": "RETURN",
        "frame_index": 4
    }
]
print("Ability 595: Added IS_SELF_MOVE condition")

# Save the updated data
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\nFixed 4 abilities with missing jumps")
