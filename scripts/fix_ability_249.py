#!/usr/bin/env python3
"""
Fix ability 249 - completely wrong frames
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Fix Ability 249
ability_249 = data['abilities'][249]

# Text: "ライブ開始時手札を2枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、1枚をデッキの上に置き、1枚を控え室に置く。"
# Correct frames:
# 1. Optionally discard 2 cards from hand
# 2. Look at top 3 cards of deck
# 3. Add 1 to hand
# 4. Put 1 on top of deck
# 5. Put 1 in discard

ability_249['frames'] = [
    {
        "op": "MOVE_TO_DISCARD",
        "frame_index": 0,
        "value": 2,
        "attr": {
            "is_optional": 1,
            "target_player": "SELF"
        },
        "slot": {
            "target_slot": "HAND"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 4
    },
    {
        "op": "LOOK_DECK",
        "frame_index": 2,
        "value": 3,
        "slot": {
            "target_slot": "DECK_TOP"
        }
    },
    {
        "op": "ADD_TO_HAND",
        "frame_index": 3,
        "value": 1,
        "attr": {
            "target_player": "SELF"
        },
        "slot": {
            "target_slot": "LOOKED_CARDS"
        }
    },
    {
        "op": "MOVE_TO_DECK",
        "frame_index": 4,
        "value": 1,
        "attr": {
            "target_player": "SELF"
        },
        "slot": {
            "target_slot": "LOOKED_CARDS",
            "deck_position": "TOP"
        }
    },
    {
        "op": "MOVE_TO_DISCARD",
        "frame_index": 5,
        "value": 1,
        "attr": {
            "target_player": "SELF"
        },
        "slot": {
            "target_slot": "LOOKED_CARDS"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 6
    }
]

ability_249['frame_verification'] = {
    "verified": True,
    "notes": [
        "Fixed: Completely incorrect frames replaced with correct implementation",
        "Frame 0: MOVE_TO_DISCARD optional with value=2 for hand discard",
        "Frame 2: LOOK_DECK with value=3 to look at top 3 cards",
        "Frame 3: ADD_TO_HAND to add 1 card to hand",
        "Frame 4: MOVE_TO_DECK to put 1 card on top of deck",
        "Frame 5: MOVE_TO_DISCARD to put 1 card in discard"
    ],
    "text_mapping": {
        "手札を2枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1, value=2",
        "自分のデッキの上からカードを3枚見る": "Frame 2: LOOK_DECK with value=3",
        "その中から1枚を手札に加え": "Frame 3: ADD_TO_HAND with value=1",
        "1枚をデッキの上に置き": "Frame 4: MOVE_TO_DECK with deck_position=TOP",
        "1枚を控え室に置く": "Frame 5: MOVE_TO_DISCARD with value=1"
    }
}

print("Ability 249: Fixed completely incorrect frames")

# Save the updated data
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed Ability 249")
