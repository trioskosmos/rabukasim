import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 173-180...")

# Ability 173
ability_173 = data['abilities'][173]
ability_173['frame_verification'] = {
    "verified": False,
    "issues": [
        "Missing effect frame to make opponent's live cards require 1 more heart to succeed",
        "Frames only have COUNT_HEARTS and RETURN, but text says '相手のライブカード置き場にあるライブカード1枚は、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる'"
    ],
    "text_mapping": {
        "自分のステージにいるメンバーが持つハートに{{heart_02.png|heart02}}が合計5つ以上ある場合": "Frame 0: COUNT_HEARTS with value=5",
        "相手のライブ開始時、相手のライブカード置き場にあるライブカード1枚は、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる": "ISSUE: Missing effect frame"
    },
    "required_frames": [
        "Should have frame to increase opponent's live card heart requirement"
    ]
}

# Ability 174
ability_174 = data['abilities'][174]
ability_174['frame_verification'] = {
    "verified": True,
    "notes": [
        "If heart05 total ≥5, grant ability to increase opponent's live card heart requirement",
        "Frame 0: COUNT_HEARTS with value=5",
        "Frame 1: JUMP_IF_FALSE",
        "Frame 2: GRANT_ABILITY",
        "1 card shares this pattern (桜内梨子)"
    ],
    "text_mapping": {
        "自分のステージにいるメンバーが持つハートに{{heart_05.png|heart05}}が合計5つ以上ある場合": "Frame 0: COUNT_HEARTS with value=5",
        "相手のライブ開始時、相手のライブカード置き場にあるライブカード1枚は、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる": "Frame 2: GRANT_ABILITY"
    }
}

# Ability 175
ability_175 = data['abilities'][175]
ability_175['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: MOVE_TO_DISCARD has is_optional=1 but text doesn't say optional",
        "Missing frame to put live card from discard at 4th position from top"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを2枚控え室に置く": "Frame 0: MOVE_TO_DISCARD with value=2 (ISSUE: has is_optional=1)",
        "その後、自分の控え室からライブカード1枚を自分のデッキの一番上から4枚目に置いてもよい": "ISSUE: Missing frame"
    },
    "required_frames": [
        "MOVE_TO_DISCARD should not have is_optional=1",
        "Should have frame to place live card at 4th position"
    ]
}

# Ability 176
ability_176 = data['abilities'][176]
ability_176['frame_verification'] = {
    "verified": True,
    "notes": [
        "Look at 2 cards, put any number in any order on top, discard rest",
        "Frame 0: LOOK_REORDER_DISCARD with value=2",
        "1 card shares this pattern (百生吟子)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く": "Frame 0: LOOK_REORDER_DISCARD with value=2"
    }
}

# Ability 177
ability_177 = data['abilities'][177]
ability_177['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: MOVE_TO_DISCARD has is_optional=1 but text doesn't say optional",
        "Frame 1: GROUP_FILTER has value=4 but text says 3 cards - should be value=3",
        "Missing heart filter for heart05 in GROUP_FILTER"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを3枚控え室に置く": "Frame 0: MOVE_TO_DISCARD with value=3 (ISSUE: has is_optional=1)",
        "それらがすべて{{heart_05.png|heart05}}を持つメンバーカードの場合": "Frame 1: GROUP_FILTER with value=4 (ISSUE: should be value=3, missing heart05 filter)",
        "ライブ終了時まで、{{heart_05.png|heart05}}を得る": "Frame 3: ADD_HEARTS with heart_type=4"
    },
    "required_frames": [
        "MOVE_TO_DISCARD should not have is_optional=1",
        "GROUP_FILTER should have value=3 and heart filter for heart05"
    ]
}

# Ability 178
ability_178 = data['abilities'][178]
ability_178['frame_verification'] = {
    "verified": True,
    "notes": [
        "Mill 5 cards from deck top",
        "Frame 0: MOVE_TO_DISCARD with value=5",
        "1 card shares this pattern (黒澤ダイヤ)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを5枚控え室に置く": "Frame 0: MOVE_TO_DISCARD with value=5"
    }
}

# Ability 179
ability_179 = data['abilities'][179]
ability_179['frame_verification'] = {
    "verified": True,
    "notes": [
        "Mill 5 cards, if live card among them, draw 1",
        "Frame 0: MOVE_TO_DISCARD with value=5",
        "Frame 1: DISCARDED_CARDS with card_type=LIVE",
        "Frame 2: JUMP_IF_FALSE",
        "Frame 3: DRAW with value=1",
        "1 card shares this pattern (エマ・ヴェルデ)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを5枚控え室に置く": "Frame 0: MOVE_TO_DISCARD with value=5",
        "それらの中にライブカードがある場合、カードを1枚引く": "Frames 1-3: DISCARDED_CARDS + JUMP_IF_FALSE + DRAW"
    }
}

# Ability 180
ability_180 = data['abilities'][180]
ability_180['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: LOOK_DECK instead of LOOK_AND_CHOOSE - missing reveal=1, dest_discard=1, remainder_zone=DISCARD",
        "Frame 1 has is_optional=1 but the optional should apply to the whole operation",
        "Missing frame to discard remaining cards"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを5枚見る": "Frame 0: LOOK_DECK with value=5 (ISSUE: should be LOOK_AND_CHOOSE)",
        "その中から『Aqours』のライブカードを1枚公開して手札に加えてもよい": "Frame 0: group_id=AQOURS (ISSUE: missing reveal=1), Frame 1: ADD_TO_HAND (ISSUE: is_optional on wrong frame)",
        "残りを控え室に置く": "ISSUE: Missing frame to discard remaining cards"
    },
    "required_frames": [
        "Should use LOOK_AND_CHOOSE with reveal=1, dest_discard=1, remainder_zone=DISCARD, is_optional=1"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 173-180")
print("Saved file")
