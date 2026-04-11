import json

with open('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Fix ability #456
ab = data['abilities'][456]

# Correct frames for: "If 3+ cards in both players' success piles, gain 3 blades"
ab['frames'] = [
    {
        "op": "COUNT_SUCCESS",
        "frame_index": 0,
        "value": 3,
        "attr": {
            "target_player": "BOTH",
            "value_threshold": 3,
            "is_ge": 1
        },
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 2
    },
    {
        "op": "ADD_BLADES",
        "frame_index": 2,
        "value": 3,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 3
    }
]

with open('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed ability #456")
