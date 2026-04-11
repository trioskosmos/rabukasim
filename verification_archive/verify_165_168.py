import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 165-168...")

# Ability 165
ability_165 = data['abilities'][165]
ability_165['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 2: LOOK_DECK instead of LOOK_AND_CHOOSE - missing reveal=1, dest_discard=1, remainder_zone=DISCARD",
        "Frame 2 only filters for Liella with blade heart, but text says 'SunnyPassion OR Liella with blade heart' - missing SunnyPassion filter",
        "Missing frame to discard remaining cards"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを5枚見る": "Frame 2: LOOK_DECK with value=5 (ISSUE: should be LOOK_AND_CHOOSE)",
        "その中から『SunnyPassion』のメンバーカードかブレードハートを持つ『Liella!』のメンバーカードを1枚公開して手札に加えてもよい": "Frame 2: group_id=LIELLA, has_blade_heart=1 (ISSUE: missing SunnyPassion filter and reveal)",
        "残りを控え室に置く": "ISSUE: Missing frame to discard remaining cards"
    },
    "required_frames": [
        "Should use LOOK_AND_CHOOSE with reveal=1, dest_discard=1, remainder_zone=DISCARD",
        "Should include SunnyPassion filter (OR condition with Liella blade heart)"
    ]
}

# Ability 166
ability_166 = data['abilities'][166]
ability_166['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 1, then recover Aqours card from discard",
        "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "Frame 1: JUMP_IF_FALSE",
        "Frame 2: RECOVER_MEMBER with group_id=AQOURS",
        "1 card shares this pattern (桜内梨子)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分の控え室から『Aqours』のカードを1枚手札に加える": "Frame 2: RECOVER_MEMBER with group_id=AQOURS"
    }
}

# Ability 167
ability_167 = data['abilities'][167]
ability_167['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 1, then recover Hasunosora card from discard",
        "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "Frame 1: JUMP_IF_FALSE",
        "Frame 2: RECOVER_MEMBER with group_id=HASUNOSORA",
        "1 card shares this pattern (安養寺姫芽)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分の控え室から『蓮ノ空』のカードを1枚手札に加える": "Frame 2: RECOVER_MEMBER with group_id=HASUNOSORA"
    }
}

# Ability 168
ability_168 = data['abilities'][168]
ability_168['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 2: PLAY_MEMBER_FROM_DISCARD missing cost≤2 filter",
        "Missing group_id=AQOURS filter"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分の控え室からコスト2以下の『Aqours』のメンバーカードを1枚、メンバーのいないエリアに登場させる": "Frame 2: PLAY_MEMBER_FROM_DISCARD (ISSUE: missing cost≤2 and group_id=AQOURS filters)",
        "（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）": "Implicit in PLAY_MEMBER_FROM_DISCARD"
    },
    "required_frames": [
        "PLAY_MEMBER_FROM_DISCARD should have cost≤2 and group_id=AQOURS filters"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 165-168")
print("Saved file")
