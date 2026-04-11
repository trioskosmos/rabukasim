import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 101...")

ability_101 = data['abilities'][101]
ability_101['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 5: MOVE_MEMBER has value=1, but text says '2人まで' (up to 2 members)",
        "Frame 4: SELECT_MEMBER can select up to 2, but MOVE_MEMBER only processes 1 member",
        "Missing loop or different frame logic to tap all selected members",
        "Frame 2: SUM_VALUE purpose unclear - may be related to selection count"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "相手のステージにいるコスト4以下のメンバーを2人までウェイトにする": "Frame 4: SELECT_MEMBER with value=2, cost≤4 (ISSUE: Frame 5 only taps 1)"
    },
    "required_frames": [
        "MOVE_MEMBER should have value matching selected count, or loop through selected members"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 101 - marked as unverified due to frame issue")
print("Saved file")
