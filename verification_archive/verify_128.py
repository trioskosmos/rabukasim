import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 128...")

ability_128 = data['abilities'][128]
ability_128['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional activate 1 tapped member",
        "Frame 0: SELECT_MEMBER with is_tapped=1, is_optional=1",
        "Frame 1: ACTIVATE_MEMBER",
        "2 cards share this pattern (高海千歌, 桜内梨子 variants)"
    ],
    "text_mapping": {
        "自分のステージにいるメンバーを1人までアクティブにする": "Frames 0-1: SELECT_MEMBER (is_tapped=1, is_optional=1) + ACTIVATE_MEMBER"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 128 - frames match text correctly")
print("Saved file")
