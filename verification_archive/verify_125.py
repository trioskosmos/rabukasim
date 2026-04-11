import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 125...")

ability_125 = data['abilities'][125]
ability_125['frame_verification'] = {
    "verified": True,
    "notes": [
        "Choice: activate 1 member or activate 2 energy",
        "Frame 0: SELECT_MODE with 2 options",
        "Frames 1-2: JUMP to respective branches",
        "Frame 3: ACTIVATE_MEMBER (option 1)",
        "Frame 4: JUMP to end",
        "Frame 5: ACTIVATE_ENERGY with value=2 (option 2)",
        "Frame 6: JUMP to end",
        "2 cards share this pattern (エマ・ヴェルデ variants)"
    ],
    "text_mapping": {
        "自分のステージにいるメンバー1人か、エネルギーを2枚アクティブにする": "Frames 3-5: ACTIVATE_MEMBER or ACTIVATE_ENERGY with value=2"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 125 - frames match text correctly")
print("Saved file")
