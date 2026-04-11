import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 189-200...")

# Ability 189 - duplicate of 188
ability_189 = data['abilities'][189]
ability_189['frame_verification'] = {
    "verified": True,
    "notes": [
        "Duplicate of ability 188 - optional tap self, then tap 1 opponent cost≤4 member",
        "6 cards share this pattern"
    ],
    "text_mapping": {
        "このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする": "Frames 0-3: SET_TAPPED + JUMP_IF_FALSE + SELECT_MEMBER + MOVE_MEMBER"
    }
}

# Ability 190
ability_190 = data['abilities'][190]
ability_190['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select heart01/03/06, gain selected heart per success live card",
        "Frame 0: COLOR_SELECT with color_mask=RED|GREEN|ANY",
        "Frame 1: ADD_HEARTS with compare_accumulated=1, remainder_zone=SUCCESS_PILE, is_dynamic=1, heart_type=SELECTED",
        "5 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ": "Frame 0: COLOR_SELECT",
        "ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、選んだハートを1つ得る": "Frame 1: ADD_HEARTS with dynamic based on SUCCESS_PILE"
    }
}

# Ability 191
ability_191 = data['abilities'][191]
ability_191['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 2: ADD_HEARTS missing target selection for '自分のステージにいるこのメンバー以外のメンバー1人'",
        "Text specifies targeting a specific member (not this member), but frame just adds hearts without targeting"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "ライブ終了時まで、自分のステージにいるこのメンバー以外のメンバー1人は、{{heart_01.png|heart01}}を得る": "Frame 2: ADD_HEARTS (ISSUE: missing target selection)"
    },
    "required_frames": [
        "ADD_HEARTS should target specific member (not this member)"
    ]
}

# Ability 192
ability_192 = data['abilities'][192]
ability_192['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 2: ADD_HEARTS missing target selection for group-matched member",
        "Text says 'これにより控え室に置いたカードと同じグループ名を持つメンバー1人' but frame doesn't target specific member"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "ライブ終了時まで、これにより控え室に置いたカードと同じグループ名を持つメンバー1人は、{{heart_01.png|heart01}}を得る": "Frame 2: ADD_HEARTS (ISSUE: missing group filter and target selection)"
    },
    "required_frames": [
        "ADD_HEARTS should target member with same group as discarded card"
    ]
}

# Ability 193
ability_193 = data['abilities'][193]
ability_193['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: PAY_ENERGY but text says 'このメンバーをウェイトにするか、手札を1枚控え室に置く'",
        "Should use SELECT_MODE with two options instead of PAY_ENERGY"
    ],
    "text_mapping": {
        "{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにするか、手札を1枚控え室に置く": "ISSUE: Frame 0 uses PAY_ENERGY instead of SELECT_MODE",
        "エネルギーを1枚アクティブにする": "Missing ACTIVATE_ENERGY frame"
    },
    "required_frames": [
        "Should use SELECT_MODE with two options: SET_TAPPED or MOVE_TO_DISCARD, then ACTIVATE_ENERGY"
    ]
}

# Ability 194
ability_194 = data['abilities'][194]
ability_194['frame_verification'] = {
    "verified": True,
    "notes": [
        "Activate all Liella members and all energy",
        "Frame 0: ACTIVATE_MEMBER with group_id=LIELLA, value=99",
        "Frame 1: ACTIVATE_ENERGY with value=99",
        "4 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{center.png|センター}}自分のステージにいるすべての『Liella!』のメンバーと、自分のすべてのエネルギーをアクティブにする": "Frames 0-1: ACTIVATE_MEMBER + ACTIVATE_ENERGY"
    }
}

# Ability 195
ability_195 = data['abilities'][195]
ability_195['frame_verification'] = {
    "verified": True,
    "notes": [
        "If left and right side members have same cost, tap all opponent members with blade≤3",
        "Frame 0: SYNC_COST",
        "Frame 1: JUMP_IF_FALSE",
        "Frame 2: TAP_OPPONENT with filter=BLADE_LE3",
        "4 cards share this pattern"
    ],
    "text_mapping": {
        "自分のステージの右サイドエリアと左サイドエリアにいるメンバーのコストが同じ場合": "Frame 0: SYNC_COST",
        "相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のすべてのメンバーをウェイトにする": "Frame 2: TAP_OPPONENT with filter=BLADE_LE3"
    }
}

# Ability 196
ability_196 = data['abilities'][196]
ability_196['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy, gain blade per live card in stage",
        "Frame 0: PAY_ENERGY with is_optional=1",
        "Frame 2: SUM_VALUE",
        "Frame 3: GROUP_FILTER",
        "Frame 5: ADD_BLADES with compare_accumulated=1, remainder_zone=STAGE, is_dynamic=1",
        "4 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY with is_optional=1",
        "ライブ終了時まで、自分のライブ中のカード1枚につき、{{icon_blade.png|ブレード}}を得る": "Frame 5: ADD_BLADES with dynamic based on STAGE"
    }
}

# Ability 197
ability_197 = data['abilities'][197]
ability_197['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy, select heart color, gain that heart",
        "Frame 0: PAY_ENERGY with is_optional=1",
        "Frame 2: COLOR_SELECT with is_optional=1",
        "Frame 3: ADD_HEARTS with heart_type=SELECTED",
        "4 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY with is_optional=1",
        "好きなハートの色を1つ指定する": "Frame 2: COLOR_SELECT",
        "ライブ終了時まで、そのハートを1つ得る": "Frame 3: ADD_HEARTS with heart_type=SELECTED"
    }
}

# Ability 198
ability_198 = data['abilities'][198]
ability_198['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: SELECT_MEMBER missing group_id=MUSE filter",
        "Frame 4: ADD_HEARTS has is_optional=1 but should not be optional (effect is guaranteed after paying cost)",
        "Frame 4: ADD_HEARTS has target_player=BOTH but text says '自分のステージ' (should be SELF)"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}『μ's』のメンバー1人をウェイトにしてもよい": "Frame 0: SELECT_MEMBER (ISSUE: missing group_id=MUSE)",
        "ライブ終了時まで、{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る": "Frame 4: ADD_HEARTS (ISSUE: has is_optional=1, target_player=BOTH should be SELF)"
    },
    "required_frames": [
        "SELECT_MEMBER should have group_id=MUSE",
        "ADD_HEARTS should not have is_optional=1",
        "ADD_HEARTS should have target_player=SELF"
    ]
}

# Ability 199
ability_199 = data['abilities'][199]
ability_199['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: HAS_KEYWORD with char_id_1=LANZHU but text says 'このターン、自分のステージにメンバーが2回以上登場している場合'",
        "Wrong condition - should check for 2+ member plays this turn, not LANZHU character"
    ],
    "text_mapping": {
        "このターン、自分のステージにメンバーが2回以上登場している場合": "ISSUE: Frame 0 uses HAS_KEYWORD with char_id_1=LANZHU instead of checking play count",
        "ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る": "Frame 2: BOOST_SCORE"
    },
    "required_frames": [
        "Should use PLAY_COUNT or similar to check for 2+ member plays this turn"
    ]
}

# Ability 200
ability_200 = data['abilities'][200]
ability_200['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional position change this member",
        "Frame 0: MOVE_MEMBER with destination=POSITION_CHANGE, is_optional=1",
        "4 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}このメンバーをポジションチェンジしてもよい": "Frame 0: MOVE_MEMBER with destination=POSITION_CHANGE, is_optional=1"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 189-200")
print("Saved file")
