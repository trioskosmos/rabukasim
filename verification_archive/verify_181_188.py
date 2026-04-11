import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 181-188...")

# Ability 181
ability_181 = data['abilities'][181]
ability_181['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: LOOK_AND_CHOOSE missing dest_discard=1 and remainder_zone=DISCARD",
        "Text says '残りを控え室に置く' but frame doesn't handle this"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを5枚見る": "Frame 0: LOOK_AND_CHOOSE value.count=5, reveal=1",
        "その中から『μ's』のライブカードを1枚公開して手札に加えてもよい": "Frame 0: group_id=MUSE, is_optional=1",
        "残りを控え室に置く": "ISSUE: Frame 0 missing dest_discard=1, remainder_zone=DISCARD"
    },
    "required_frames": [
        "LOOK_AND_CHOOSE should have dest_discard=1, remainder_zone=DISCARD"
    ]
}

# Ability 182
ability_182 = data['abilities'][182]
ability_182['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: LOOK_AND_CHOOSE missing remainder_zone=DISCARD",
        "Text says '残りを控え室に置く' but frame doesn't handle this"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを5枚見る": "Frame 0: LOOK_AND_CHOOSE value.count=5, reveal=1, dest_discard=1",
        "その中から『虹ヶ咲』のライブカードを1枚まで公開して手札に加えてもよい": "Frame 0: group_id=NIJIGASAKI, is_optional=1",
        "残りを控え室に置く": "ISSUE: Frame 0 missing remainder_zone=DISCARD"
    },
    "required_frames": [
        "LOOK_AND_CHOOSE should have remainder_zone=DISCARD"
    ]
}

# Ability 183
ability_183 = data['abilities'][183]
ability_183['frame_verification'] = {
    "verified": True,
    "notes": [
        "If success live pile has 2+ cards, recover 1 live from discard",
        "Frame 0: COUNT_SUCCESS_LIVE with value=2",
        "Frame 1: JUMP_IF_FALSE",
        "Frame 2: RECOVER_LIVE",
        "1 card shares this pattern (高坂穂乃果)"
    ],
    "text_mapping": {
        "自分の成功ライブカード置き場にカードが2枚以上ある場合": "Frame 0: COUNT_SUCCESS_LIVE with value=2",
        "自分の控え室からライブカードを1枚手札に加える": "Frame 2: RECOVER_LIVE"
    }
}

# Ability 184
ability_184 = data['abilities'][184]
ability_184['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: RECOVER_MEMBER has is_optional=1 but text doesn't say optional"
    ],
    "text_mapping": {
        "自分の控え室からコスト4以下の『μ's』のメンバーカードを1枚手札に加える": "Frame 0: RECOVER_MEMBER with cost≤4, group_id=MUSE (ISSUE: has is_optional=1)"
    },
    "required_frames": [
        "RECOVER_MEMBER should not have is_optional=1"
    ]
}

# Ability 185
ability_185 = data['abilities'][185]
ability_185['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: RECOVER_MEMBER has is_optional=1 but text doesn't say optional"
    ],
    "text_mapping": {
        "自分の控え室からメンバーカードを1枚手札に加える": "Frame 0: RECOVER_MEMBER (ISSUE: has is_optional=1)"
    },
    "required_frames": [
        "RECOVER_MEMBER should not have is_optional=1"
    ]
}

# Ability 186
ability_186 = data['abilities'][186]
ability_186['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional put 1 card from discard to deck top",
        "Frame 0: SELECT_CARDS with is_optional=1",
        "Frame 1: MOVE_TO_DECK with remainder_zone=DECK_TOP",
        "1 card shares this pattern (天王寺璃奈)"
    ],
    "text_mapping": {
        "自分の控え室にあるカード1枚をデッキの一番上に置いてもよい": "Frames 0-1: SELECT_CARDS + MOVE_TO_DECK with is_optional=1"
    }
}

# Ability 187
ability_187 = data['abilities'][187]
ability_187['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy at live start to gain 2 blades until end",
        "Frame 0: PAY_ENERGY with is_optional=1",
        "Frame 1: JUMP_IF_FALSE",
        "Frame 2: ADD_BLADES with value=2",
        "12 cards share this pattern"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY with is_optional=1",
        "ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frame 2: ADD_BLADES with value=2"
    }
}

# Ability 188
ability_188 = data['abilities'][188]
ability_188['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional tap self, then tap 1 opponent cost≤4 member",
        "Frame 0: SET_TAPPED with is_optional=1",
        "Frame 1: JUMP_IF_FALSE",
        "Frame 2: SELECT_MEMBER with cost≤4, target_player=OPPONENT",
        "Frame 3: MOVE_MEMBER with is_wait=1",
        "6 cards share this pattern"
    ],
    "text_mapping": {
        "このメンバーをウェイトにしてもよい": "Frame 0: SET_TAPPED with is_optional=1",
        "相手のステージにいるコスト4以下のメンバー1人をウェイトにする": "Frames 2-3: SELECT_MEMBER + MOVE_MEMBER with cost≤4"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 181-188")
print("Saved file")
