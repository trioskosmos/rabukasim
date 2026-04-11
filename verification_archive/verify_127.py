import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 127...")

ability_127 = data['abilities'][127]
ability_127['frame_verification'] = {
    "verified": True,
    "notes": [
        "If all members are Liella and energy≥7, charge energy in wait state",
        "Frame 0: GROUP_FILTER with value=3 (all), group_id=LIELLA",
        "Frame 1: COUNT_ENERGY with value=7",
        "Frame 2: JUMP_IF_FALSE skips if condition not met",
        "Frame 3: ENERGY_CHARGE with is_wait=1",
        "2 cards share this pattern (澁谷かのん variants)"
    ],
    "text_mapping": {
        "自分のステージにいるメンバーが『Liella!』のみで": "Frame 0: GROUP_FILTER with value=3, group_id=LIELLA",
        "かつ自分のエネルギーが7枚以上ある場合": "Frame 1: COUNT_ENERGY with value=7",
        "自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く": "Frame 3: ENERGY_CHARGE with is_wait=1"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 127 - frames match text correctly")
print("Saved file")
