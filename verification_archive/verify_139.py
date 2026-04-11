import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 139...")

ability_139 = data['abilities'][139]
ability_139['frame_verification'] = {
    "verified": False,
    "issues": [
        "Missing DRAW frame",
        "Text says 'カードを1枚引く' (draw 1 card) but there's no DRAW frame",
        "Frame 2 is NOP which appears to be a placeholder for missing DRAW"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを3枚控え室に置く": "Frame 0: MOVE_TO_DISCARD with value=3",
        "それらがすべてメンバーカードの場合": "Frame 1: GROUP_FILTER with value=3, card_type=MEMBER",
        "カードを1枚引く": "ISSUE: Missing DRAW frame (Frame 2 is NOP placeholder)"
    },
    "required_frames": [
        "Should have DRAW frame instead of NOP"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 139 - marked as unverified due to missing DRAW frame")
print("Saved file")
