import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 161-164...")

# Ability 161 (duplicate of 160)
ability_161 = data['abilities'][161]
ability_161['frame_verification'] = {
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

# Ability 162
ability_162 = data['abilities'][162]
ability_162['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 2: LOOK_AND_CHOOSE missing reveal=1 for '公開して'",
        "Missing dest_discard=1 and remainder_zone=DISCARD for '残りを控え室に置く'"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを5枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=5",
        "その中から『5yncri5e!』のカードを1枚公開して手札に加えてもよい": "Frame 2: unit_id=SYNCRISE (ISSUE: missing reveal=1)",
        "残りを控え室に置く": "ISSUE: Frame 2 missing dest_discard=1, remainder_zone=DISCARD"
    },
    "required_frames": [
        "LOOK_AND_CHOOSE should have reveal=1, dest_discard=1, remainder_zone=DISCARD"
    ]
}

# Ability 163
ability_163 = data['abilities'][163]
ability_163['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 2: LOOK_AND_CHOOSE missing reveal=1 for '公開して'",
        "Missing dest_discard=1 and remainder_zone=DISCARD for '残りを控え室に置く'"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを5枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=5",
        "その中から『CatChu!』のカードを1枚公開して手札に加えてもよい": "Frame 2: unit_id=CATCHU (ISSUE: missing reveal=1)",
        "残りを控え室に置く": "ISSUE: Frame 2 missing dest_discard=1, remainder_zone=DISCARD"
    },
    "required_frames": [
        "LOOK_AND_CHOOSE should have reveal=1, dest_discard=1, remainder_zone=DISCARD"
    ]
}

# Ability 164
ability_164 = data['abilities'][164]
ability_164['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 2: LOOK_AND_CHOOSE missing reveal=1 for '公開して'",
        "Missing dest_discard=1 and remainder_zone=DISCARD for '残りを控え室に置く'"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを5枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=5",
        "その中から『KALEIDOSCORE』のカードを1枚公開して手札に加えてもよい": "Frame 2: unit_id=KALEIDOSCORE (ISSUE: missing reveal=1)",
        "残りを控え室に置く": "ISSUE: Frame 2 missing dest_discard=1, remainder_zone=DISCARD"
    },
    "required_frames": [
        "LOOK_AND_CHOOSE should have reveal=1, dest_discard=1, remainder_zone=DISCARD"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 161-164")
print("Saved file")
