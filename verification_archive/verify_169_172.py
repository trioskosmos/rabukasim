import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 169-172...")

# Ability 169
ability_169 = data['abilities'][169]
ability_169['frame_verification'] = {
    "verified": True,
    "notes": [
        "Tap 1 opponent cost≤4 member",
        "Frame 0: TAP_OPPONENT with cost≤4",
        "1 card shares this pattern (園田海未)"
    ],
    "text_mapping": {
        "相手のステージにいるコスト4以下のメンバー1人をウェイトにする": "Frame 0: TAP_OPPONENT with cost≤4"
    }
}

# Ability 170
ability_170 = data['abilities'][170]
ability_170['frame_verification'] = {
    "verified": True,
    "notes": [
        "Draw 1 card per 6 energy",
        "Frame 0: COUNT_ENERGY with value=6",
        "Frame 1: JUMP_IF_FALSE",
        "Frame 2: DRAW with per_card=ENERGY, divisor=6",
        "1 card shares this pattern (澁谷かのん)"
    ],
    "text_mapping": {
        "自分のエネルギー6枚につき、カードを1枚引く": "Frames 0-2: COUNT_ENERGY + DRAW with per_card=ENERGY, divisor=6"
    }
}

# Ability 171
ability_171 = data['abilities'][171]
ability_171['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional place 1 energy under this member, then draw 2",
        "Frame 0: PLACE_ENERGY_UNDER_MEMBER with is_optional=1",
        "Frame 1: JUMP_IF_FALSE",
        "Frame 2: DRAW with value=2",
        "1 card shares this pattern (上原歩夢)"
    ],
    "text_mapping": {
        "自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい": "Frame 0: PLACE_ENERGY_UNDER_MEMBER with is_optional=1",
        "そうした場合、カードを2枚引く": "Frame 2: DRAW with value=2"
    }
}

# Ability 172
ability_172 = data['abilities'][172]
ability_172['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: HAS_MEMBER missing char filters for '大沢瑠璃乃' (Rurino), '百生吟子' (Ginko), '徒町小鈴' (Shioru)",
        "Text says specific characters but frame has no char filters"
    ],
    "text_mapping": {
        "自分のステージに「大沢瑠璃乃」か「百生吟子」か「徒町小鈴」がいる場合": "Frame 0: HAS_MEMBER (ISSUE: missing char filters)",
        "エネルギーを1枚アクティブにし": "Frame 2: ACTIVATE_ENERGY with value=1",
        "自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える": "Frame 3: RECOVER_LIVE with group_id=HASUNOSORA"
    },
    "required_frames": [
        "HAS_MEMBER should have char_id filters for Rurino, Ginko, or Shioru"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 169-172")
print("Saved file")
