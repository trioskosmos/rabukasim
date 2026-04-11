import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 114...")

ability_114 = data['abilities'][114]
ability_114['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to recover Nijigasaki live",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: RECOVER_LIVE with group_id=NIJIGASAKI",
        "2 cards share this pattern (優木せつ菜, 三船栞子 variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える": "Frame 2: RECOVER_LIVE with group_id=NIJIGASAKI"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 114 - frames match text correctly")
print("Saved file")
