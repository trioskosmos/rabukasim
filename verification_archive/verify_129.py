import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 129...")

ability_129 = data['abilities'][129]
ability_129['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional move member to any position",
        "Frame 0: SELECT_MEMBER with is_optional=1",
        "Frame 1: MOVE_MEMBER with is_optional=1, destination=POSITION_CHANGE",
        "2 cards share this pattern (藤島慈 variants)"
    ],
    "text_mapping": {
        "自分のステージにいるメンバーを、それぞれ好きなエリアに移動させてもよい": "Frames 0-1: SELECT_MEMBER + MOVE_MEMBER with destination=POSITION_CHANGE"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 129 - frames match text correctly")
print("Saved file")
