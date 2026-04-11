import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 154-160...")

# Ability 154
ability_154 = data['abilities'][154]
ability_154['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional position change this member",
        "Frame 0: MOVE_MEMBER with is_optional=1, destination=POSITION_CHANGE",
        "1 card shares this pattern (唐可可)"
    ],
    "text_mapping": {
        "このメンバーをポジションチェンジしてもよい": "Frame 0: MOVE_MEMBER with is_optional=1, destination=POSITION_CHANGE"
    }
}

# Ability 155
ability_155 = data['abilities'][155]
ability_155['frame_verification'] = {
    "verified": True,
    "notes": [
        "Draw 1, can't live until end",
        "Frame 0: DRAW with value=1",
        "Frame 1: RESTRICTION",
        "1 card shares this pattern (大沢瑠璃乃)"
    ],
    "text_mapping": {
        "カードを1枚引く": "Frame 0: DRAW with value=1",
        "ライブ終了時まで、自分はライブできない": "Frame 1: RESTRICTION"
    }
}

# Ability 156
ability_156 = data['abilities'][156]
ability_156['frame_verification'] = {
    "verified": True,
    "notes": [
        "Gain +1 score ability until end",
        "Frame 0: GRANT_ABILITY",
        "1 card shares this pattern (平安名すみれ)"
    ],
    "text_mapping": {
        "ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る": "Frame 0: GRANT_ABILITY"
    }
}

# Ability 157
ability_157 = data['abilities'][157]
ability_157['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional play cost≤4 Liella member from hand",
        "Frame 0: SELECT_CARDS with group_id=LIELLA, cost≤4, is_optional=1",
        "Frame 1: PLAY_MEMBER_FROM_HAND",
        "1 card shares this pattern (唐可可)"
    ],
    "text_mapping": {
        "手札からコスト4以下の『Liella!』のメンバーカードを1枚ステージに登場させてもよい": "Frames 0-1: SELECT_CARDS + PLAY_MEMBER_FROM_HAND"
    }
}

# Ability 158
ability_158 = data['abilities'][158]
ability_158['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard Hasunosora card from hand, then recover member from discard",
        "Frame 0: MOVE_TO_DISCARD with group_id=HASUNOSORA, is_optional=1",
        "Frame 1: JUMP_IF_FALSE",
        "Frame 2: RECOVER_MEMBER",
        "1 card shares this pattern (百生吟子)"
    ],
    "text_mapping": {
        "手札の『蓮ノ空』のカードを1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分の控え室からメンバーカードを1枚手札に加える": "Frame 2: RECOVER_MEMBER"
    }
}

# Ability 159
ability_159 = data['abilities'][159]
ability_159['frame_verification'] = {
    "verified": False,
    "issues": [
        "Missing frame to move revealed card to success live pile",
        "Text says 'そうした場合、これにより公開したカードを自分の成功ライブカード置き場に置く' but there's no frame for this"
    ],
    "text_mapping": {
        "手札のライブカードを1枚公開してもよい": "Frame 0: REVEAL_CARDS with card_type=LIVE, is_optional=1",
        "自分の成功ライブカード置き場にあるカードを1枚手札に加える": "Frame 3: ADD_TO_HAND",
        "そうした場合、これにより公開したカードを自分の成功ライブカード置き場に置く": "ISSUE: Missing frame to move revealed card to success live pile"
    },
    "required_frames": [
        "Should have frame to move revealed card to success live pile"
    ]
}

# Ability 160
ability_160 = data['abilities'][160]
ability_160['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 2: LOOK_DECK instead of LOOK_AND_CHOOSE - missing reveal=1, dest_discard=1, remainder_zone=DISCARD",
        "Frame 3: ADD_TO_HAND missing heart filter for heart05 or heart06",
        "Missing frame to discard remaining cards"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを4枚見る": "Frame 2: LOOK_DECK with value=4 (ISSUE: should be LOOK_AND_CHOOSE)",
        "その中からハートに{{heart_05.png|heart05}}か{{heart_06.png|heart06}}を持つメンバーカードを1枚公開して手札に加えてもよい": "Frame 3: ADD_TO_HAND (ISSUE: missing heart filter and reveal)",
        "残りを控え室に置く": "ISSUE: Missing frame to discard remaining cards"
    },
    "required_frames": [
        "Should use LOOK_AND_CHOOSE with reveal=1, dest_discard=1, remainder_zone=DISCARD",
        "ADD_TO_HAND should have heart filter for heart05 or heart06"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 154-160")
print("Saved file")
