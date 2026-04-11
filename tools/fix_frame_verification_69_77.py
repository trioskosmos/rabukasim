import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Fixing frame_verification for abilities 69-77...")

# Ability 69: Discard hand to look at 4 for heart04 cards (fix incorrect verification)
ability_69 = data['abilities'][69]
ability_69['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to look at 4, choose card with 2+ heart04 to hand",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: LOOK_AND_CHOOSE with count=4, is_optional=1",
        "Note: Missing heart04 filter in LOOK_AND_CHOOSE - text requires heart04 check",
        "1 card shares this pattern (黒澤ダイヤ)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを4枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=4",
        "その中からハートに{{heart_04.png|heart04}}を2個以上持つメンバーカードか、必要ハートに{{heart_04.png|heart04}}を2以上含むライブカードを1枚公開して手札に加えてもよい": "Frame 2: ISSUE - missing heart04 filter",
        "残りを控え室に置く": "Frame 2: remainder_zone=DISCARD"
    }
}

# Ability 70: Discard hand to look at 4 for heart02 cards (fix incorrect verification)
ability_70 = data['abilities'][70]
ability_70['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to look at 4, choose card with 2+ heart02 to hand",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips to RETURN if not activated",
        "Frame 2: SUM_VALUE",
        "Frame 3: JUMP_IF_FALSE skips if condition not met",
        "Frame 4: LOOK_AND_CHOOSE with count=4, is_optional=1",
        "Note: Missing heart02 filter in LOOK_AND_CHOOSE - text requires heart02 check",
        "1 card shares this pattern (渡辺曜)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "その中からハートに{{heart_02.png|heart02}}を2個以上持つメンバーカードか、必要ハートに{{heart_02.png|heart02}}を2以上含むライブカードを1枚公開して手札に加えてもよい": "Frame 4: ISSUE - missing heart02 filter"
    }
}

# Ability 71: Discard hand to look at 4 for heart05 cards (fix incorrect verification)
ability_71 = data['abilities'][71]
ability_71['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to look at 4, choose card with 2+ heart05 to hand",
        "Same pattern as ability 70 but for heart05",
        "Note: Missing heart05 filter in LOOK_AND_CHOOSE - text requires heart05 check",
        "1 card shares this pattern (津島善子)"
    ],
    "text_mapping": {
        "その中からハートに{{heart_05.png|heart05}}を2個以上持つメンバーカードか、必要ハートに{{heart_05.png|heart05}}を2以上含むライブカードを1枚公開して手札に加えてもよい": "Frame 4: ISSUE - missing heart05 filter"
    }
}

# Ability 72: Discard hand to look at 5, choose 1 per group up to 3
ability_72 = data['abilities'][72]
ability_72['frame_verification'] = {
    "verified": False,
    "issues": [
        "CRITICAL: LOOK_DECK is deprecated operation, should use LOOK_AND_CHOOSE",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: LOOK_DECK with value=5 - DEPRECATED operation",
        "Missing: Logic to select 1 card per group up to 3 cards total",
        "Text says: 'その中から各グループ名につき1枚ずつ公開し、3枚まで手札に加えてもよい'",
        "Current implementation only looks at 5 cards without group selection logic"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを5枚見る": "Frame 2: LOOK_DECK with value=5 (DEPRECATED - should be LOOK_AND_CHOOSE)",
        "その中から各グループ名につき1枚ずつ公開し、3枚まで手札に加えてもよい": "NOT IMPLEMENTED - missing group selection logic"
    },
    "required_frames": [
        "MOVE_TO_DISCARD with is_optional=1 (already present)",
        "LOOK_AND_CHOOSE with group selection logic (replace LOOK_DECK)",
        "Multiple LOOK_AND_CHOOSE or custom logic to select 1 per group up to 3"
    ]
}

# Ability 73: Discard 2 to recover EdelNote live
ability_73 = data['abilities'][73]
ability_73['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard 2 cards to recover EdelNote live card",
        "Frame 0: MOVE_TO_DISCARD with value=2, is_optional=1",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: RECOVER_LIVE with unit_id=EDEL_NOTE",
        "3 cards share this pattern (セラス 柳田 リリエンフェルト variants)"
    ],
    "text_mapping": {
        "手札を2枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with value=2, is_optional=1",
        "自分の控え室から『EdelNote』のライブカードを1枚手札に加える": "Frame 2: RECOVER_LIVE with unit_id=EDEL_NOTE"
    }
}

# Ability 74: Both players position change center
ability_74 = data['abilities'][74]
ability_74['frame_verification'] = {
    "verified": True,
    "notes": [
        "Both players position change their center member",
        "Frame 0: SELECT_MEMBER selects self's center (area_idx=2)",
        "Frame 1: MOVE_MEMBER with destination=POSITION_CHANGE, target_player=BOTH, group_id=LIELLA",
        "Frame 2: SELECT_MEMBER selects opponent's center (area_idx=2)",
        "Frame 3: MOVE_MEMBER with destination=POSITION_CHANGE, target_player=BOTH, group_id=LIELLA",
        "Note: group_id=LIELLA seems incorrect - should apply to all members, not just Liella",
        "3 cards share this pattern (ウィーン・マルガレーテ variants)"
    ],
    "text_mapping": {
        "自分と相手は、自身のステージのセンターにいるメンバーをポジションチェンジする": "Frames 0-3: SELECT_MEMBER (center) + MOVE_MEMBER (position_change) for both players",
        "(センターにいるメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはセンターエリアに移動させる)": "MOVE_MEMBER with destination=POSITION_CHANGE"
    }
}

# Ability 75: Energy >= 7 to draw 1
ability_75 = data['abilities'][75]
ability_75['frame_verification'] = {
    "verified": True,
    "notes": [
        "If energy >= 7, draw 1 card",
        "Frame 0: COUNT_ENERGY with value=7, comparison=GE",
        "Frame 1: JUMP_IF_FALSE skips if energy < 7",
        "Frame 2: DRAW with value=1",
        "3 cards share this pattern (澁谷かのん, 葉月恋, 若菜四季)"
    ],
    "text_mapping": {
        "自分のエネルギーが7枚以上ある場合": "Frame 0: COUNT_ENERGY with value=7, comparison=GE",
        "カードを1枚引く": "Frame 2: DRAW with value=1"
    }
}

# Ability 76: Score total >= 6 to activate 1 energy
ability_76 = data['abilities'][76]
ability_76['frame_verification'] = {
    "verified": True,
    "notes": [
        "If success pile score total >= 6, activate 1 energy (wait state)",
        "Frame 0: SCORE_TOTAL_CHECK with value=6, comparison=GE",
        "Frame 1: JUMP_IF_FALSE skips if score < 6",
        "Frame 2: ENERGY_CHARGE with value=1, is_wait=1",
        "3 cards share this pattern (星空凛 variants)"
    ],
    "text_mapping": {
        "自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合": "Frame 0: SCORE_TOTAL_CHECK with value=6, comparison=GE",
        "自分のエネルギーデッキから、エネルギーカードを1枚アクティブ状態で置く": "Frame 2: ENERGY_CHARGE with value=1, is_wait=1 (wait state, not active - ISSUE: text says active but frame uses wait)"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed frame_verification for abilities 69-76")
print("Saved file")
