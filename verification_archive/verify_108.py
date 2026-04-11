import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 108...")

ability_108 = data['abilities'][108]
ability_108['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 4: LOOK_AND_CHOOSE has reveal=1 but missing dest_discard=1 and remainder_zone=DISCARD",
        "Text says '残りを控え室に置く' (put the rest in discard) but frame doesn't handle this"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを5枚見る": "Frame 4: LOOK_AND_CHOOSE value.count=5",
        "その中から『Liella!』のカードを1枚まで公開して手札に加えてもよい": "Frame 4: group_id=LIELLA, reveal=1, is_optional=1",
        "残りを控え室に置く": "ISSUE: Frame 4 missing dest_discard=1, remainder_zone=DISCARD"
    },
    "required_frames": [
        "LOOK_AND_CHOOSE should have: dest_discard=1, remainder_zone=DISCARD"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 108 - marked as unverified due to missing discard logic")
print("Saved file")
