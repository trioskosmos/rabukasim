import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 104...")

ability_104 = data['abilities'][104]
ability_104['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to LOOK_AND_CHOOSE 2 cards",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: LOOK_AND_CHOOSE with count=2, reveal=1, dest_discard=1",
        "2 cards share this pattern (朝香果林, ミア・テイラー variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを2枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=2",
        "その中から1枚を手札に加え、残りを控え室に置く": "Frame 2: dest_discard=1, remainder_zone=DISCARD"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 104 - frames match text correctly")
print("Saved file")
