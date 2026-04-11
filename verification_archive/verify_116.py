import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 116...")

ability_116 = data['abilities'][116]
ability_116['frame_verification'] = {
    "verified": True,
    "notes": [
        "Tap 1 opponent with ≤1 original blade",
        "Frame 0: TAP_OPPONENT with value=1, filter=BLADE_LE1",
        "2 cards share this pattern (矢澤にこ variants)"
    ],
    "text_mapping": {
        "相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が1つ以下のメンバー1人をウェイトにする": "Frame 0: TAP_OPPONENT with filter=BLADE_LE1"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 116 - frames match text correctly")
print("Saved file")
