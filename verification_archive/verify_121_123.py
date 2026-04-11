import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 121-123...")

# Ability 121
ability_121 = data['abilities'][121]
ability_121['frame_verification'] = {
    "verified": True,
    "notes": [
        "Energy charge in wait state",
        "Frame 0: ENERGY_CHARGE with is_wait=1",
        "2 cards share this pattern (葉月恋 variants)"
    ],
    "text_mapping": {
        "自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く": "Frame 0: ENERGY_CHARGE with is_wait=1"
    }
}

# Ability 122
ability_122 = data['abilities'][122]
ability_122['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional place 2 energy under member",
        "Frame 0: PLACE_ENERGY_UNDER_MEMBER with value=2, is_optional=1",
        "2 cards share this pattern (中須かすみ variants)"
    ],
    "text_mapping": {
        "自分のエネルギー置き場にあるエネルギー2枚をこのメンバーの下に置いてもよい": "Frame 0: PLACE_ENERGY_UNDER_MEMBER with value=2, is_optional=1"
    }
}

# Ability 123
ability_123 = data['abilities'][123]
ability_123['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: ACTIVATE_MEMBER missing group_id=PRINTEMPS filter",
        "Text specifies 'Printemps' but frame doesn't filter for this group"
    ],
    "text_mapping": {
        "自分のステージにいる『Printemps』のメンバーを1人までアクティブにする": "Frame 0: ACTIVATE_MEMBER with is_optional=1 (ISSUE: missing group_id=PRINTEMPS filter)"
    },
    "required_frames": [
        "ACTIVATE_MEMBER should have group_id=PRINTEMPS to filter for Printemps members"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 121-123")
print("Saved file")
