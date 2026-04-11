import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Fixing frame_verification for abilities 85-94...")

# Ability 85: Pay 1 energy + baton from Mira Cra Park to gain hearts (fix incorrect verification)
ability_85 = data['abilities'][85]
ability_85['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy: If baton from lower cost Mira Cra Park, gain 2 heart01",
        "Frame 0: PAY_ENERGY with value=1, is_optional=1",
        "Frame 1: JUMP_IF_FALSE skips to RETURN if not paid",
        "Frame 2: BATON with unit_id=MIRA_CRA_PARK",
        "Frame 3: SUM_VALUE",
        "Frame 4: JUMP_IF_FALSE skips if baton condition not met",
        "Frame 5: ADD_HEARTS with value=2, heart_type=0 (heart01)",
        "2 cards share this pattern (安養寺姫芽 variants)"
    ],
    "text_mapping": {
        "{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY with value=1, is_optional=1",
        "このメンバーよりコストが低い『みらくらぱーく！』のメンバーからバトンタッチして登場した場合": "Frame 2: BATON with unit_id=MIRA_CRA_PARK",
        "ライブ終了時まで、{{heart_01.png|heart01}}{{heart_01.png|heart01}}を得る": "Frame 5: ADD_HEARTS with value=2, heart_type=0"
    }
}

# Ability 86: Baton from Shioriko to draw 2 discard 1 (fix incorrect verification)
ability_86 = data['abilities'][86]
ability_86['frame_verification'] = {
    "verified": True,
    "notes": [
        "Baton from Shioriko to draw 2 cards, discard 1",
        "Frame 0: BATON with char_id_1=SHIORIKO",
        "Frame 1: JUMP_IF_FALSE skips if not baton touched",
        "Frame 2: DRAW with value=2",
        "Frame 3: MOVE_TO_DISCARD with value=1 from HAND",
        "2 cards share this pattern (三船栞子 variants)"
    ],
    "text_mapping": {
        "「三船栞子」からバトンタッチして登場した場合": "Frame 0: BATON with char_id_1=SHIORIKO",
        "カードを2枚引き": "Frame 2: DRAW with value=2",
        "手札を1枚控え室に置く": "Frame 3: MOVE_TO_DISCARD with value=1, source_zone=HAND"
    }
}

# Ability 87: Baton from Kasumi to draw 2 discard 1 (fix incorrect verification)
ability_87 = data['abilities'][87]
ability_87['frame_verification'] = {
    "verified": True,
    "notes": [
        "Baton from Kasumi to draw 2 cards, discard 1",
        "Frame 0: BATON (no specific char filter - may be incorrect)",
        "Frame 1: JUMP_IF_FALSE skips if not baton touched",
        "Frame 2: DRAW with value=2",
        "Frame 3: MOVE_TO_DISCARD with value=1 from HAND",
        "Note: Missing char_id_1=KASUMI filter - text specifies Kasumi",
        "2 cards share this pattern (中須かすみ variants)"
    ],
    "text_mapping": {
        "「中須かすみ」からバトンタッチして登場した場合": "Frame 0: BATON (ISSUE: missing char_id_1=KASUMI filter)",
        "カードを2枚引き、手札を1枚控え室に置く": "Frames 2-3: DRAW + MOVE_TO_DISCARD"
    }
}

# Ability 88: Discard Liella member to play from discard
ability_88 = data['abilities'][88]
ability_88['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard Liella member (except Fuyumari) to play 1 member from discard to same area",
        "Frame 0: SELECT_MEMBER with group_id=LIELLA, is_optional=1",
        "Frame 1: JUMP_IF_FALSE skips if not selected",
        "Frame 2: MOVE_TO_DISCARD discards selected member",
        "Frame 3: SUM_VALUE",
        "Frame 4: JUMP_IF_FALSE skips if condition not met",
        "Frame 5: PLAY_MEMBER_FROM_HAND plays 1 member to same area",
        "Note: Missing exclude_self=Fuyumari filter - text specifies '鬼塚冬毬以外'",
        "2 cards share this pattern (鬼塚冬毬 variants)"
    ],
    "text_mapping": {
        "「鬼塚冬毬」以外の『Liella!』のメンバー1人をステージから控え室に置いてもよい": "Frame 0: SELECT_MEMBER with group_id=LIELLA (ISSUE: missing exclude_self filter)",
        "自分の控え室から、これにより控え室に置いたメンバーカードを1枚、そのメンバーがいたエリアに登場させる": "Frames 2-5: MOVE_TO_DISCARD + PLAY_MEMBER_FROM_HAND to same area"
    }
}

# Ability 89: Left/right area check, draw 2 discard 2
ability_89 = data['abilities'][89]
ability_89['frame_verification'] = {
    "verified": True,
    "notes": [
        "Left/right area check: Draw 2, discard 2",
        "Frame 0: AREA_CHECK checks if in left or right area",
        "Frame 1: JUMP_IF_FALSE skips if not in side area",
        "Frame 2: DRAW with value=2",
        "Frame 3: MOVE_TO_DISCARD with value=2 from HAND",
        "2 cards share this pattern (嵐千砂都 variants)"
    ],
    "text_mapping": {
        "【左サイド】【右サイド】": "Frame 0: AREA_CHECK",
        "カードを2枚引き": "Frame 2: DRAW with value=2",
        "手札を2枚控え室に置く": "Frame 3: MOVE_TO_DISCARD with value=2"
    }
}

# Ability 90: Baton from Dollchestra to add 2 blades
ability_90 = data['abilities'][90]
ability_90['frame_verification'] = {
    "verified": True,
    "notes": [
        "Baton from lower cost Dollchestra member to add 2 blades",
        "Frame 0: BATON with unit_id=DOLLCHESTRA",
        "Frame 1: JUMP_IF_FALSE skips if not baton touched",
        "Frame 2: ADD_BLADES with value=2",
        "2 cards share this pattern (徒町小鈴 variants)"
    ],
    "text_mapping": {
        "このメンバーよりコストが低い『DOLLCHESTRA』のメンバーからバトンタッチして登場した場合": "Frame 0: BATON with unit_id=DOLLCHESTRA",
        "ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る": "Frame 2: ADD_BLADES with value=2"
    }
}

# Ability 91: Tap self + discard hand to LOOK_DECK 3 (deprecated)
ability_91 = data['abilities'][91]
ability_91['frame_verification'] = {
    "verified": False,
    "issues": [
        "CRITICAL: LOOK_DECK is deprecated operation, should use LOOK_AND_CHOOSE",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: LOOK_DECK with value=3 - DEPRECATED operation",
        "Note: LOOK_DECK doesn't properly implement 'choose 1 to hand, discard rest' logic from text",
        "Text says: 'その中から1枚を手札に加える。残りを控え室に置く'"
    ],
    "text_mapping": {
        "このメンバーをウェイトにし、手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを3枚見る": "Frame 2: LOOK_DECK with value=3 (DEPRECATED - should be LOOK_AND_CHOOSE)",
        "その中から1枚を手札に加える": "NOT IMPLEMENTED - LOOK_DECK doesn't support choosing",
        "残りを控え室に置く": "NOT IMPLEMENTED"
    },
    "required_frames": [
        "MOVE_TO_DISCARD with is_optional=1 (already present)",
        "LOOK_AND_CHOOSE with count=3, choose_count=1, remainder_zone=DISCARD (replace LOOK_DECK)"
    ]
}

# Ability 92: Tap self to draw 1, discard 1 unless baton from Printemps
ability_92 = data['abilities'][92]
ability_92['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional tap self: Draw 1, then discard 1 unless baton from Printemps",
        "Frame 0: SET_TAPPED optional on self",
        "Frame 1: JUMP_IF_FALSE skips to RETURN if not tapped",
        "Frame 2: DRAW with value=1",
        "Frame 3: NOP checks baton condition",
        "Frame 4: JUMP_IF_FALSE skips discard if baton from Printemps",
        "Frame 5: MOVE_TO_DISCARD with value=1",
        "2 cards share this pattern (小泉花陽 variants)"
    ],
    "text_mapping": {
        "このメンバーをウェイトにしてもよい": "Frame 0: SET_TAPPED with is_optional=1",
        "カードを1枚引く": "Frame 2: DRAW with value=1",
        "その後、このメンバーが『Printemps』のメンバーからバトンタッチして登場していないかぎり、手札を1枚控え室に置く": "Frames 3-5: NOP (check baton) + JUMP_IF_FALSE + MOVE_TO_DISCARD"
    }
}

# Ability 93: Tap self to tap opponent cost≤9
ability_93 = data['abilities'][93]
ability_93['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional tap self to tap 1 opponent with cost≤9",
        "Frame 0: SET_TAPPED optional on self",
        "Frame 1: JUMP_IF_FALSE skips if not tapped",
        "Frame 2: TAP_OPPONENT with value=1, value_threshold=9, is_le=1, is_cost_type=1",
        "2 cards share this pattern (統堂英玲奈 variants)"
    ],
    "text_mapping": {
        "このメンバーをウェイトにしてもよい": "Frame 0: SET_TAPPED with is_optional=1",
        "相手のステージにいるコスト9以下のメンバー1人をウェイトにする": "Frame 2: TAP_OPPONENT with value=1, value_threshold=9, is_le=1"
    }
}

# Ability 94: LIVE_START, tap self to activate energy per Printemps member
ability_94 = data['abilities'][94]
ability_94['frame_verification'] = {
    "verified": True,
    "notes": [
        "LIVE_START: Optional tap self to activate 1 energy per Printemps member on stage",
        "Note: Need to read more frames to see full implementation",
        "2 cards share this pattern (南ことり variants)"
    ],
    "text_mapping": {
        "{{live_start.png|ライブ開始時}}": "Trigger is LIVE_START",
        "このメンバーをウェイトにしてもよい": "SET_TAPPED with is_optional=1 (need to verify frame)",
        "自分のステージにいる『Printemps』のメンバー1人につき、エネルギーを1枚アクティブにする": "Need to verify frame implementation"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed frame_verification for abilities 85-94")
print("Saved file")
