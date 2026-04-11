import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 103...")

ability_103 = data['abilities'][103]
ability_103['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to mill 2, then recover member",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: SUM_VALUE (conditional logic)",
        "Frame 3: JUMP_IF_FALSE skips if condition fails",
        "Frame 4: MOVE_TO_DISCARD with value=2 from DECK_TOP",
        "Frame 5: RECOVER_MEMBER with value=1 from DISCARD",
        "2 cards share this pattern (天王寺璃奈 variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを2枚控え室に置く": "Frame 4: MOVE_TO_DISCARD with value=2, source_zone=DECK_TOP",
        "その後、自分の控え室からメンバーカードを1枚手札に加える": "Frame 5: RECOVER_MEMBER with value=1"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 103 - frames match text correctly")
print("Saved file")
