import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 102...")

ability_102 = data['abilities'][102]
ability_102['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 2: HAS_MEMBER only has special_id='Not Self' but text specifies 'コスト11' (cost 11)",
        "Missing cost filter - should have value_enabled=1, value_threshold=11, is_cost_type=1"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のステージにこのメンバー以外のコスト11のメンバーがいる場合": "Frame 2: HAS_MEMBER with special_id=Not Self (ISSUE: missing cost=11 filter)",
        "自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える": "Frame 4: RECOVER_LIVE with group_id=NIJIGASAKI"
    },
    "required_frames": [
        "HAS_MEMBER should include cost filter: value_enabled=1, value_threshold=11, is_cost_type=1"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 102 - marked as unverified due to missing cost filter")
print("Saved file")
