#!/usr/bin/env python3
"""
Fix Ability 524 - missing MOVE_TO_DISCARD for hand discard option
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

# Fix Ability 524
ability_524 = data['abilities'][524]
semantic_524 = semantic_data['abilities'][524]

# Text: "登場/ライブ開始時E支払ってもよい：以下から1つを選ぶ。・相手のステージにいるコスト4以下のメンバー1人をウェイトにする。・カードを1枚引く。起動ターン1回このメンバーをウェイトにするか、手札を1枚控え室に置く：エネルギーを1枚アクティブにする。"
# This is a two-part ability. The second part has two options: tap self OR discard hand card
# The frames only show the first part (optional energy payment with mode select)
# Need to add the second part with the self-tap or hand-discard option

ability_524['frames'] = [
    {
        "op": "PAY_ENERGY",
        "frame_index": 0,
        "attr": {
            "is_optional": 1
        },
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 5
    },
    {
        "op": "SELECT_MODE",
        "frame_index": 2,
        "attr": {
            "options": ["TAP_COST_4_MEMBER", "DRAW_CARD"]
        }
    },
    {
        "op": "JUMP",
        "frame_index": 3,
        "value": 2
    },
    {
        "op": "JUMP",
        "frame_index": 4,
        "value": 1
    },
    {
        "op": "SELECT_MEMBER",
        "frame_index": 5,
        "attr": {
            "target_player": "OPPONENT",
            "max_cost": 4
        },
        "slot": {
            "target_slot": "STAGE"
        }
    },
    {
        "op": "SET_TAPPED",
        "frame_index": 6,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "JUMP",
        "frame_index": 7,
        "value": 3
    },
    {
        "op": "DRAW",
        "frame_index": 8,
        "value": 1,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 9
    },
    # Second part: self tap or hand discard
    {
        "op": "SELECT_MODE",
        "frame_index": 10,
        "attr": {
            "once_per_turn": 1,
            "options": ["TAP_SELF", "DISCARD_HAND"]
        }
    },
    {
        "op": "JUMP",
        "frame_index": 11,
        "value": 2
    },
    {
        "op": "JUMP",
        "frame_index": 12,
        "value": 1
    },
    {
        "op": "SET_TAPPED",
        "frame_index": 13,
        "attr": {
            "target_player": "SELF"
        },
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "ACTIVATE_ENERGY",
        "frame_index": 14,
        "attr": {
            "target_player": "SELF"
        },
        "slot": {
            "target_slot": "ENERGY"
        }
    },
    {
        "op": "JUMP",
        "frame_index": 15,
        "value": 2
    },
    {
        "op": "MOVE_TO_DISCARD",
        "frame_index": 16,
        "value": 1,
        "attr": {
            "target_player": "SELF",
            "is_optional": 1
        },
        "slot": {
            "target_slot": "HAND"
        }
    },
    {
        "op": "ACTIVATE_ENERGY",
        "frame_index": 17,
        "attr": {
            "target_player": "SELF"
        },
        "slot": {
            "target_slot": "ENERGY"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 18
    }
]

print("Ability 524: Added missing second part with self-tap or hand-discard options")

# Save the updated data
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed Ability 524")
