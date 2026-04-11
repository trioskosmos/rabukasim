import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 109...")

ability_109 = data['abilities'][109]
ability_109['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 4: LOOK_AND_CHOOSE is missing dest_discard=1 and remainder_zone=DISCARD",
        "Text says '残りを控え室に置く' (put the rest in discard) but frame doesn't handle this",
        "Also missing reveal=1 for '公開して' (reveal)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを5枚見る": "Frame 4: LOOK_AND_CHOOSE value.count=5",
        "その中から『Liella!』のメンバーカードを1枚公開して手札に加えてもよい": "Frame 4: card_type=MEMBER, group_id=LIELLA, is_optional=1 (ISSUE: missing reveal=1)",
        "残りを控え室に置く": "ISSUE: Frame 4 missing dest_discard=1, remainder_zone=DISCARD"
    },
    "required_frames": [
        "LOOK_AND_CHOOSE should have: dest_discard=1, remainder_zone=DISCARD, reveal=1"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 109 - marked as unverified due to missing discard logic")
print("Saved file")
