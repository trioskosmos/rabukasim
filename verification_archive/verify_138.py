import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 138...")

ability_138 = data['abilities'][138]
ability_138['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: MOVE_TO_DISCARD has is_optional=1 but text doesn't say 'optional'",
        "Frame 1: GROUP_FILTER with value=4 doesn't check for heart04 specifically",
        "Text requires cards to have heart04, but frame only checks if all are member cards"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを3枚控え室に置く": "Frame 0: MOVE_TO_DISCARD with value=3 (ISSUE: has is_optional=1)",
        "それらがすべて{{heart_04.png|heart04}}を持つメンバーカードの場合": "Frame 1: GROUP_FILTER (ISSUE: doesn't check for heart04)",
        "ライブ終了時まで、{{heart_04.png|heart04}}を得る": "Frame 3: ADD_HEARTS with heart_type=3"
    },
    "required_frames": [
        "MOVE_TO_DISCARD should not have is_optional=1",
        "Should use DISCARDED_CARDS with heart filter instead of GROUP_FILTER"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 138 - marked as unverified due to frame issues")
print("Saved file")
