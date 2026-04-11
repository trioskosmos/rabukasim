import json

with open('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Fix ability #387
ab = data['abilities'][387]

# Replace RECOVER_LIVE frame with LOOK_AND_CHOOSE from Yell zone
ab['frames'] = [
    {
        "op": "LOOK_AND_CHOOSE",
        "frame_index": 0,
        "value": {"look_count": 0, "choose_count": 1},
        "attr": {
            "is_optional": 1,
            "card_type": "LIVE"
        },
        "slot": {
            "target_slot": "HAND",
            "source_zone": "YELL"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 1
    }
]

with open('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed ability #387")
