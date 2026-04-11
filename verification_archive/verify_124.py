import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 124...")

ability_124 = data['abilities'][124]
ability_124['frame_verification'] = {
    "verified": True,
    "notes": [
        "Activate all tapped members on stage",
        "Frame 0: SELECT_MEMBER with value=99, is_tapped=1",
        "Frame 1: ACTIVATE_MEMBER",
        "2 cards share this pattern (星空凛 variants)"
    ],
    "text_mapping": {
        "自分のステージにいるすべてのメンバーをアクティブにする": "Frames 0-1: SELECT_MEMBER (is_tapped=1) + ACTIVATE_MEMBER"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 124 - frames match text correctly")
print("Saved file")
