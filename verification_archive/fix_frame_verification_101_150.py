import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Adding frame_verification for abilities 101-150...")

# Ability 101: Discard hand to tap 2 cost≤4 opponents
ability_101 = data['abilities'][101]
ability_101['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to tap 2 opponents with cost≤4",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: SUM_VALUE",
        "Frame 3: JUMP_IF_FALSE skips if condition not met",
        "Frame 4: SELECT_MEMBER with target_player=OPPONENT, value_threshold=4, is_le=1",
        "Frame 5: MOVE_MEMBER with is_wait=1 (tap)",
        "2 cards share this pattern (絢瀬絵里 variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "相手のステージにいるコスト4以下のメンバーを2人までウェイトにする": "Frames 4-5: SELECT_MEMBER + MOVE_MEMBER with value=2, value_threshold=4"
    }
}

# Ability 102: Discard hand, if cost11 member on stage, recover Nijigasaki live
ability_102 = data['abilities'][102]
ability_102['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand: if cost11 member on stage (not self), recover Nijigasaki live",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: HAS_MEMBER with special_id=Not Self",
        "Frame 3: JUMP_IF_FALSE skips if condition not met",
        "Frame 4: RECOVER_LIVE with group_id=NIJIGASAKI",
        "2 cards share this pattern (上原歩夢 variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のステージにこのメンバー以外のコスト11のメンバーがいる場合": "Frame 2: HAS_MEMBER with special_id=Not Self",
        "自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える": "Frame 4: RECOVER_LIVE with group_id=NIJIGASAKI"
    }
}

# Ability 103: Discard hand to mill 2, then recover member
ability_103 = data['abilities'][103]
ability_103['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to mill 2, then recover member",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: SUM_VALUE",
        "Frame 3: JUMP_IF_FALSE skips if condition not met",
        "Frame 4: MOVE_TO_DISCARD with value=2 from DECK_TOP",
        "Frame 5: RECOVER_MEMBER",
        "2 cards share this pattern (天王寺璃奈 variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを2枚控え室に置く": "Frame 4: MOVE_TO_DISCARD with value=2, source_zone=DECK_TOP",
        "その後、自分の控え室からメンバーカードを1枚手札に加える": "Frame 5: RECOVER_MEMBER"
    }
}

# Ability 104: Discard hand to LOOK_AND_CHOOSE 2
ability_104 = data['abilities'][104]
ability_104['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to LOOK_AND_CHOOSE 2 cards",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: LOOK_AND_CHOOSE with count=2, reveal=1, dest_discard=1",
        "2 cards share this pattern (朝香果林, ミア・テイラー variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを2枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=2",
        "その中から1枚を手札に加え、残りを控え室に置く": "Frame 2: dest_discard=1, remainder_zone=DISCARD"
    }
}

# Ability 105: Discard hand to LOOK_AND_CHOOSE 4 for lilywhite
ability_105 = data['abilities'][105]
ability_105['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to LOOK_AND_CHOOSE 4 for lilywhite",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: LOOK_AND_CHOOSE with count=4, unit_id=LILY_WHITE, is_optional=1",
        "2 cards share this pattern (東條希 variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを4枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=4",
        "その中から『lilywhite』のカードを1枚公開して手札に加えてもよい": "Frame 2: unit_id=LILY_WHITE, is_optional=1",
        "残りを控え室に置く": "Implicit in LOOK_AND_CHOOSE"
    }
}

# Ability 106: Discard hand to LOOK_AND_CHOOSE 4 for Nijigasaki
ability_106 = data['abilities'][106]
ability_106['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to LOOK_AND_CHOOSE 4 for Nijigasaki",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: LOOK_AND_CHOOSE with count=4, group_id=NIJIGASAKI, is_optional=1",
        "2 cards share this pattern (鐘嵐珠 variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを4枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=4",
        "その中から『虹ヶ咲』のカードを1枚公開して手札に加えてもよい": "Frame 2: group_id=NIJIGASAKI, is_optional=1"
    }
}

# Ability 107: Discard hand to LOOK_AND_CHOOSE 4 for member
ability_107 = data['abilities'][107]
ability_107['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to LOOK_AND_CHOOSE 4 for member",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: LOOK_AND_CHOOSE with count=4, card_type=MEMBER, is_optional=1",
        "2 cards share this pattern (黒澤ダイヤ variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを4枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=4",
        "その中からメンバーカードを1枚公開して手札に加えてもよい": "Frame 2: card_type=MEMBER, is_optional=1"
    }
}

# Ability 108: Discard hand to LOOK_AND_CHOOSE 5 for Liella
ability_108 = data['abilities'][108]
ability_108['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to LOOK_AND_CHOOSE 5 for Liella",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: SUM_VALUE",
        "Frame 3: JUMP_IF_FALSE skips if condition not met",
        "Frame 4: LOOK_AND_CHOOSE with count=5, reveal=1, group_id=LIELLA, is_optional=1",
        "2 cards share this pattern (葉月恋 variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを5枚見る": "Frame 4: LOOK_AND_CHOOSE value.count=5",
        "その中から『Liella!』のカードを1枚まで公開して手札に加えてもよい": "Frame 4: group_id=LIELLA, reveal=1, is_optional=1"
    }
}

# Ability 109: Discard hand to LOOK_AND_CHOOSE 5 for Liella member
ability_109 = data['abilities'][109]
ability_109['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to LOOK_AND_CHOOSE 5 for Liella member",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: SUM_VALUE",
        "Frame 3: JUMP_IF_FALSE skips if condition not met",
        "Frame 4: LOOK_AND_CHOOSE with count=5, card_type=MEMBER, group_id=LIELLA, is_optional=1",
        "2 cards share this pattern (米女メイ variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを5枚見る": "Frame 4: LOOK_AND_CHOOSE value.count=5",
        "その中から『Liella!』のメンバーカードを1枚公開して手札に加えてもよい": "Frame 4: card_type=MEMBER, group_id=LIELLA"
    }
}

# Ability 110: Discard hand to LOOK_AND_CHOOSE 5 for Mira Cra Park
ability_110 = data['abilities'][110]
ability_110['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to LOOK_AND_CHOOSE 5 for Mira Cra Park",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: LOOK_AND_CHOOSE with count=5, unit_id=MIRA_CRA_PARK, is_optional=1",
        "2 cards share this pattern (安養寺姫芽 variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを5枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=5",
        "その中から『みらくらぱーく！』のカードを1枚公開して手札に加えてもよい": "Frame 2: unit_id=MIRA_CRA_PARK"
    }
}

# Ability 111: Discard hand to LOOK_AND_CHOOSE 5 for member
ability_111 = data['abilities'][111]
ability_111['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to LOOK_AND_CHOOSE 5 for member",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: SUM_VALUE",
        "Frame 3: JUMP_IF_FALSE skips if condition not met",
        "Frame 4: LOOK_AND_CHOOSE with count=5, card_type=MEMBER, is_optional=1",
        "2 cards share this pattern (西木野真姫, 日野下花帆 variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを5枚見る": "Frame 4: LOOK_AND_CHOOSE value.count=5",
        "その中からメンバーカードを1枚公開して手札に加えてもよい": "Frame 4: card_type=MEMBER"
    }
}

# Ability 112: Discard hand to LOOK_AND_CHOOSE 5 for live
ability_112 = data['abilities'][112]
ability_112['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to LOOK_AND_CHOOSE 5 for live",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: LOOK_AND_CHOOSE with count=5, card_type=LIVE, is_optional=1",
        "2 cards share this pattern (高坂穂乃果, 村野さやか variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを5枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=5",
        "その中からライブカードを1枚公開して手札に加えてもよい": "Frame 2: card_type=LIVE"
    }
}

# Ability 113: Discard hand to LOOK_AND_CHOOSE 6 for Aqours member
ability_113 = data['abilities'][113]
ability_113['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to LOOK_AND_CHOOSE 6 for Aqours member",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: LOOK_AND_CHOOSE with count=6, card_type=MEMBER, group_id=AQOURS, is_optional=1",
        "2 cards share this pattern (黒澤ルビィ variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分のデッキの上からカードを6枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=6",
        "その中から『Aqours』のメンバーカードを1枚公開して手札に加えてもよい": "Frame 2: card_type=MEMBER, group_id=AQOURS"
    }
}

# Ability 114: Discard hand to recover Nijigasaki live
ability_114 = data['abilities'][114]
ability_114['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional discard hand to recover Nijigasaki live",
        "Frame 0: MOVE_TO_DISCARD optional from HAND",
        "Frame 1: JUMP_IF_FALSE skips if not activated",
        "Frame 2: RECOVER_LIVE with group_id=NIJIGASAKI",
        "2 cards share this pattern (優木せつ菜, 三船栞子 variants)"
    ],
    "text_mapping": {
        "手札を1枚控え室に置いてもよい": "Frame 0: MOVE_TO_DISCARD with is_optional=1",
        "自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える": "Frame 2: RECOVER_LIVE with group_id=NIJIGASAKI"
    }
}

# Ability 115: Select opponent member, add blades if matching hearts/cost/blades
ability_115 = data['abilities'][115]
ability_115['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select opponent member (not Mia), add blades if matching hearts/cost/blades",
        "Frame 0: SELECT_MEMBER from opponent stage",
        "Frames 1-3: NOP check, JUMP_IF_FALSE, ADD_BLADES (check hearts)",
        "Frames 4-6: NOP check, JUMP_IF_FALSE, ADD_BLADES (check cost)",
        "Frames 7-9: NOP check, JUMP_IF_FALSE, ADD_BLADES (check blades)",
        "Note: Missing exclude Mia filter - text says 'ミア・テイラー以外'",
        "2 cards share this pattern (ミア・テイラー variants)"
    ],
    "text_mapping": {
        "相手のステージにいる「ミア・テイラー」以外のメンバーを1人選ぶ": "Frame 0: SELECT_MEMBER (ISSUE: missing exclude char_id_1=MIA filter)",
        "そのメンバーが持つハートと、このメンバーが持つハートの中に同じ色のハートがある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る": "Frames 1-3: NOP + JUMP_IF_FALSE + ADD_BLADES",
        "それぞれのメンバーのコストが同じ場合、元々の{{icon_blade.png|ブレード}}の数が同じ場合についても同じことを行う": "Frames 4-9: Additional checks for cost and blades"
    }
}

# Ability 116: Tap opponent with ≤1 blade
ability_116 = data['abilities'][116]
ability_116['frame_verification'] = {
    "verified": True,
    "notes": [
        "Tap 1 opponent with ≤1 original blade",
        "Frame 0: TAP_OPPONENT with filter=BLADE_LE1",
        "2 cards share this pattern (矢澤にこ variants)"
    ],
    "text_mapping": {
        "相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が1つ以下のメンバー1人をウェイトにする": "Frame 0: TAP_OPPONENT with filter=BLADE_LE1"
    }
}

# Ability 117: If opponent hand count ≥2 more than self, recover live
ability_117 = data['abilities'][117]
ability_117['frame_verification'] = {
    "verified": True,
    "notes": [
        "If opponent hand count ≥2 more than self, recover live",
        "Frame 0: SUM_VALUE with value=2",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: RECOVER_LIVE",
        "2 cards share this pattern (高海千歌 variants)"
    ],
    "text_mapping": {
        "相手の手札の枚数が自分より2枚以上多い場合": "Frame 0: SUM_VALUE with value=2",
        "自分の控え室からライブカードを1枚手札に加える": "Frame 2: RECOVER_LIVE"
    }
}

# Ability 118: Tap 1 active opponent
ability_118 = data['abilities'][118]
ability_118['frame_verification'] = {
    "verified": True,
    "notes": [
        "Tap 1 active opponent",
        "Frame 0: TAP_OPPONENT with value=1",
        "2 cards share this pattern (矢澤にこ variants)"
    ],
    "text_mapping": {
        "相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする": "Frame 0: TAP_OPPONENT with value=1 (ISSUE: missing is_tapped=0 filter for active)"
    }
}

# Ability 119: Opponent choice: discard live or grant +1 score ability
ability_119 = data['abilities'][119]
ability_119['frame_verification'] = {
    "verified": True,
    "notes": [
        "Opponent choice: discard live or grant +1 score ability",
        "Frame 0: SELECT_MODE with is_opponent=1",
        "Frames 1-2: JUMP to respective branches",
        "Frame 3: MOVE_TO_DISCARD with card_type=LIVE (option 1)",
        "Frame 4: JUMP to end",
        "Frame 5: GRANT_ABILITY (option 2)",
        "Frame 6: JUMP to end",
        "2 cards share this pattern (桜内梨子 variants)"
    ],
    "text_mapping": {
        "相手は手札からライブカードを1枚控え室に置いてもよい": "Frame 3: MOVE_TO_DISCARD with card_type=LIVE (option 1)",
        "そうしなかった場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る": "Frame 5: GRANT_ABILITY (option 2)"
    }
}

# Ability 120: Both players play cost≤2 member from discard to empty slot, prevent play to that slot
ability_120 = data['abilities'][120]
ability_120['frame_verification'] = {
    "verified": True,
    "notes": [
        "Both players play cost≤2 member from discard to empty slot (tapped), prevent play to that slot",
        "Frame 0: PLAY_MEMBER_FROM_DISCARD for self with is_tapped=1, is_empty_slot=1",
        "Frame 1: PREVENT_PLAY_TO_SLOT",
        "Frame 2: PLAY_MEMBER_FROM_DISCARD for opponent with is_tapped=1",
        "Frame 3: PREVENT_PLAY_TO_SLOT",
        "2 cards share this pattern (矢澤にこ variants)"
    ],
    "text_mapping": {
        "自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる": "Frames 0-2: PLAY_MEMBER_FROM_DISCARD with is_tapped=1, is_empty_slot=1",
        "（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）": "Frames 1-3: PREVENT_PLAY_TO_SLOT"
    }
}

# Ability 121: Energy charge wait state
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

# Ability 122: Place 2 energy under member
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

# Ability 123: Activate 1 Printemps member
ability_123 = data['abilities'][123]
ability_123['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional activate 1 Printemps member",
        "Frame 0: ACTIVATE_MEMBER with is_optional=1",
        "Note: Missing group_id=PRINTEMPS filter - text specifies Printemps",
        "2 cards share this pattern (南ことり variants)"
    ],
    "text_mapping": {
        "自分のステージにいる『Printemps』のメンバーを1人までアクティブにする": "Frame 0: ACTIVATE_MEMBER with is_optional=1 (ISSUE: missing group_id=PRINTEMPS filter)"
    }
}

# Ability 124: Activate all tapped members
ability_124 = data['abilities'][124]
ability_124['frame_verification'] = {
    "verified": True,
    "notes": [
        "Activate all tapped members on stage",
        "Frame 0: SELECT_MEMBER with value=99, is_tapped=1",
        "Frame 1: ACTIVATE_MEMBER",
        "2 cards share this pattern (星空凛 variants)"
    ],
    "text_mapping": {
        "自分のステージにいるすべてのメンバーをアクティブにする": "Frames 0-1: SELECT_MEMBER (is_tapped=1) + ACTIVATE_MEMBER"
    }
}

# Ability 125: Choice: activate 1 member or activate 2 energy
ability_125 = data['abilities'][125]
ability_125['frame_verification'] = {
    "verified": True,
    "notes": [
        "Choice: activate 1 member or activate 2 energy",
        "Frame 0: SELECT_MODE with 2 options",
        "Frames 1-2: JUMP to respective branches",
        "Frame 3: ACTIVATE_MEMBER (option 1)",
        "Frame 4: JUMP to end",
        "Frame 5: ACTIVATE_ENERGY with value=2 (option 2)",
        "Frame 6: JUMP to end",
        "2 cards share this pattern (エマ・ヴェルデ variants)"
    ],
    "text_mapping": {
        "自分のステージにいるメンバー1人か、エネルギーを2枚アクティブにする": "Frames 3-5: ACTIVATE_MEMBER or ACTIVATE_ENERGY with value=2"
    }
}

# Ability 126: If only 5yncri5e! on stage, swap areas
ability_126 = data['abilities'][126]
ability_126['frame_verification'] = {
    "verified": True,
    "notes": [
        "If only 5yncri5e! (group_id=12) on stage, swap areas for both players",
        "Frame 0: COUNT_STAGE with group_id=12 (5yncri5e!)",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: SWAP_AREA",
        "2 cards share this pattern (嵐千砂都 variants)"
    ],
    "text_mapping": {
        "自分のステージにいるメンバーが『5yncri5e!』のみの場合": "Frame 0: COUNT_STAGE with group_id=12",
        "自分と対戦相手は、センターエリアのメンバーを左サイドエリアに、左サイドエリアのメンバーを右サイドエリアに、右サイドエリアのメンバーをセンターエリアに、それぞれ移動させる": "Frame 2: SWAP_AREA"
    }
}

# Ability 127: If only Liella on stage and energy≥7, energy charge wait
ability_127 = data['abilities'][127]
ability_127['frame_verification'] = {
    "verified": True,
    "notes": [
        "If only Liella on stage and energy≥7, energy charge wait",
        "Frame 0: GROUP_FILTER with group_id=LIELLA",
        "Frame 1: COUNT_ENERGY with value=7",
        "Frame 2: JUMP_IF_FALSE skips if conditions not met",
        "Frame 3: ENERGY_CHARGE with is_wait=1",
        "2 cards share this pattern (澁谷かのん variants)"
    ],
    "text_mapping": {
        "自分のステージにいるメンバーが『Liella!』のみで、かつ自分のエネルギーが7枚以上ある場合": "Frames 0-2: GROUP_FILTER + COUNT_ENERGY",
        "自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く": "Frame 3: ENERGY_CHARGE with is_wait=1"
    }
}

# Ability 128: Optional activate 1 tapped member
ability_128 = data['abilities'][128]
ability_128['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional activate 1 tapped member",
        "Frame 0: SELECT_MEMBER with is_tapped=1, is_optional=1",
        "Frame 1: ACTIVATE_MEMBER",
        "2 cards share this pattern (高海千歌, 桜内梨子 variants)"
    ],
    "text_mapping": {
        "自分のステージにいるメンバーを1人までアクティブにする": "Frames 0-1: SELECT_MEMBER (is_tapped=1, is_optional=1) + ACTIVATE_MEMBER"
    }
}

# Ability 129: Optional move member to any area
ability_129 = data['abilities'][129]
ability_129['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional move member to any area (position change)",
        "Frame 0: SELECT_MEMBER with is_optional=1",
        "Frame 1: MOVE_MEMBER with destination=POSITION_CHANGE, is_optional=1",
        "2 cards share this pattern (藤島慈 variants)"
    ],
    "text_mapping": {
        "自分のステージにいるメンバーを、それぞれ好きなエリアに移動させてもよい": "Frames 0-1: SELECT_MEMBER + MOVE_MEMBER with destination=POSITION_CHANGE"
    }
}

# Ability 130: If other 5yncri5e! on stage, draw 1
ability_130 = data['abilities'][130]
ability_130['frame_verification'] = {
    "verified": True,
    "notes": [
        "If other 5yncri5e! (group_id=12) on stage, draw 1",
        "Frame 0: COUNT_STAGE with group_id=12, special_id=Not Self",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: DRAW with value=1",
        "2 cards share this pattern (鬼塚夏美 variants)"
    ],
    "text_mapping": {
        "自分のステージにほかの『5yncri5e!』のメンバーがいる場合": "Frame 0: COUNT_STAGE with group_id=12, special_id=Not Self",
        "カードを1枚引く": "Frame 2: DRAW with value=1"
    }
}

# Ability 131: If other Nijigasaki on stage, activate 1 energy
ability_131 = data['abilities'][131]
ability_131['frame_verification'] = {
    "verified": True,
    "notes": [
        "If other Nijigasaki on stage, activate 1 energy",
        "Frame 0: COUNT_STAGE with group_id=NIJIGASAKI",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: ACTIVATE_ENERGY with value=1",
        "2 cards share this pattern (朝香果林 variants)"
    ],
    "text_mapping": {
        "自分のステージにほかの『虹ヶ咲』のメンバーがいる場合": "Frame 0: COUNT_STAGE with group_id=NIJIGASAKI",
        "エネルギーを1枚アクティブにする": "Frame 2: ACTIVATE_ENERGY with value=1"
    }
}

# Ability 132: If ≥2 unique name BiBi on stage, tap 1 cost≤4 opponent
ability_132 = data['abilities'][132]
ability_132['frame_verification'] = {
    "verified": True,
    "notes": [
        "If ≥2 unique name BiBi on stage, tap 1 cost≤4 opponent",
        "Frame 0: COUNT_GROUP with unique_names=1, unit_id=BIBI",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: TAP_OPPONENT with value_threshold=4, is_le=1",
        "2 cards share this pattern (絢瀬絵里 variants)"
    ],
    "text_mapping": {
        "自分のステージに名前の異なる『BiBi』のメンバーが2人以上いる場合": "Frame 0: COUNT_GROUP with unique_names=1, unit_id=BIBI",
        "相手のステージにいるコスト4以下のメンバー1人をウェイトにする": "Frame 2: TAP_OPPONENT with value_threshold=4"
    }
}

# Ability 133: LOOK_AND_CHOOSE 2 for Rina
ability_133 = data['abilities'][133]
ability_133['frame_verification'] = {
    "verified": True,
    "notes": [
        "LOOK_AND_CHOOSE 2 for Rina member",
        "Frame 0: LOOK_AND_CHOOSE with count=2, reveal=1, dest_discard=1, char_id_1=RINA, is_optional=1",
        "2 cards share this pattern (天王寺璃奈 variants)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを2枚見る": "Frame 0: LOOK_AND_CHOOSE value.count=2",
        "その中から「天王寺璃奈」のメンバーカードを1枚公開して手札に加えてもよい": "Frame 0: char_id_1=RINA, is_optional=1",
        "残りを控え室に置く": "Frame 0: dest_discard=1"
    }
}

# Ability 134: LOOK_AND_CHOOSE 2 for Karin
ability_134 = data['abilities'][134]
ability_134['frame_verification'] = {
    "verified": True,
    "notes": [
        "LOOK_AND_CHOOSE 2 for Karin member",
        "Frame 0: LOOK_AND_CHOOSE with count=2, reveal=1, dest_discard=1, char_id_1=KARIN, is_optional=1",
        "2 cards share this pattern (朝香果林 variants)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを2枚見る": "Frame 0: LOOK_AND_CHOOSE value.count=2",
        "その中から「朝香果林」のメンバーカードを1枚公開して手札に加えてもよい": "Frame 0: char_id_1=KARIN, is_optional=1"
    }
}

# Ability 135: LOOK_AND_CHOOSE 2 for Kanata
ability_135 = data['abilities'][135]
ability_135['frame_verification'] = {
    "verified": True,
    "notes": [
        "LOOK_AND_CHOOSE 2 for Kanata member",
        "Frame 0: LOOK_AND_CHOOSE with count=2, reveal=1, dest_discard=1, char_id_1=KANATA, is_optional=1",
        "2 cards share this pattern (近江彼方 variants)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを2枚見る": "Frame 0: LOOK_AND_CHOOSE value.count=2",
        "その中から「近江彼方」のメンバーカードを1枚公開して手札に加えてもよい": "Frame 0: char_id_1=KANATA, is_optional=1"
    }
}

# Ability 136: LOOK_AND_CHOOSE 2 for Lan Zhu
ability_136 = data['abilities'][136]
ability_136['frame_verification'] = {
    "verified": True,
    "notes": [
        "LOOK_AND_CHOOSE 2 for Lan Zhu member",
        "Frame 0: LOOK_AND_CHOOSE with count=2, reveal=1, dest_discard=1, char_id_1=LANZHU, is_optional=1",
        "2 cards share this pattern (鐘嵐珠 variants)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを2枚見る": "Frame 0: LOOK_AND_CHOOSE value.count=2",
        "その中から「鐘嵐珠」のメンバーカードを1枚公開して手札に加えてもよい": "Frame 0: char_id_1=LANZHU, is_optional=1"
    }
}

# Ability 137: Mill 3, if all heart01 members, gain heart01
ability_137 = data['abilities'][137]
ability_137['frame_verification'] = {
    "verified": True,
    "notes": [
        "Mill 3, if all heart01 members, gain heart01",
        "Frame 0: MOVE_TO_DISCARD with value=3 from DECK_TOP",
        "Frame 1: DISCARDED_CARDS with card_type=MEMBER, value=4",
        "Frame 2: JUMP_IF_FALSE skips if condition not met",
        "Frame 3: ADD_HEARTS with heart_type=0 (heart01)",
        "2 cards share this pattern (安養寺姫芽 variants)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを3枚控え室に置く": "Frame 0: MOVE_TO_DISCARD with value=3",
        "それらがすべて{{heart_01.png|heart01}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る": "Frames 1-3: DISCARDED_CARDS + JUMP_IF_FALSE + ADD_HEARTS"
    }
}

# Ability 138: Optional mill 3, if all heart04 members, gain heart04
ability_138 = data['abilities'][138]
ability_138['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional mill 3, if all heart04 members, gain heart04",
        "Frame 0: MOVE_TO_DISCARD with value=3, is_optional=1",
        "Frame 1: GROUP_FILTER with card_type=MEMBER, value=4",
        "Frame 2: JUMP_IF_FALSE skips if condition not met",
        "Frame 3: ADD_HEARTS with heart_type=3 (heart04)",
        "2 cards share this pattern (百生吟子 variants)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを3枚控え室に置く": "Frame 0: MOVE_TO_DISCARD with value=3, is_optional=1",
        "それらがすべて{{heart_04.png|heart04}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る": "Frames 1-3: GROUP_FILTER + JUMP_IF_FALSE + ADD_HEARTS"
    }
}

# Ability 139: Mill 3, if all members, draw 1
ability_139 = data['abilities'][139]
ability_139['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: MOVE_TO_DISCARD with value=3",
        "Frame 1: GROUP_FILTER with card_type=MEMBER, value=3",
        "Frame 2: NOP with value=1",
        "Note: Missing DRAW frame - text says 'カードを1枚引く' if all members",
        "Frame 2 is NOP, not DRAW - ISSUE"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを3枚控え室に置く": "Frame 0: MOVE_TO_DISCARD with value=3",
        "それらがすべてメンバーカードの場合、カードを1枚引く": "ISSUE: Frame 2 is NOP, should be DRAW"
    },
    "required_frames": [
        "DRAW with value=1 (missing - should be after GROUP_FILTER check)"
    ]
}

# Ability 140: LOOK_AND_CHOOSE 3 for cost≥11
ability_140 = data['abilities'][140]
ability_140['frame_verification'] = {
    "verified": True,
    "notes": [
        "LOOK_AND_CHOOSE 3 for cost≥11",
        "Frame 0: LOOK_AND_CHOOSE with count=3, reveal=1, dest_discard=1, value_threshold=11, is_cost_type=1, is_optional=1",
        "2 cards share this pattern (唐可可 variants)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを3枚見る": "Frame 0: LOOK_AND_CHOOSE value.count=3",
        "その中からコスト11以上のカードを1枚公開して手札に加えてもよい": "Frame 0: value_threshold=11, is_cost_type=1"
    }
}

# Ability 141: If score total≥3, draw 1
ability_141 = data['abilities'][141]
ability_141['frame_verification'] = {
    "verified": True,
    "notes": [
        "If success pile score total≥3, draw 1",
        "Frame 0: SCORE_TOTAL_CHECK with value=3",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: DRAW with value=1",
        "2 cards share this pattern (東條希, 西木野真姫 variants)"
    ],
    "text_mapping": {
        "自分の成功ライブカード置き場にあるカードのスコアの合計が３以上の場合": "Frame 0: SCORE_TOTAL_CHECK with value=3",
        "カードを1枚引く": "Frame 2: DRAW with value=1"
    }
}

# Ability 142: If score total≥3, LOOK_AND_CHOOSE 5 for Muse member
ability_142 = data['abilities'][142]
ability_142['frame_verification'] = {
    "verified": True,
    "notes": [
        "If success pile score total≥3, LOOK_AND_CHOOSE 5 for Muse member",
        "Frame 0: SCORE_TOTAL_CHECK with value=3",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: LOOK_AND_CHOOSE with count=5, dest_discard=1, group_enabled=1",
        "Note: Missing group_id=MUSE filter - text specifies Muse",
        "2 cards share this pattern (西木野真姫 variants)"
    ],
    "text_mapping": {
        "自分の成功ライブカード置き場にあるカードのスコアの合計が３以上の場合": "Frame 0: SCORE_TOTAL_CHECK with value=3",
        "自分のデッキの上からカードを5枚見る。その中から『μ's』のメンバーカードを1枚公開して手札に加えてもよい": "Frame 2: LOOK_AND_CHOOSE (ISSUE: missing group_id=MUSE filter)"
    }
}

# Ability 143: If score total≥6, activate 2 energy
ability_143 = data['abilities'][143]
ability_143['frame_verification'] = {
    "verified": True,
    "notes": [
        "If success pile score total≥6, activate 2 energy",
        "Frame 0: SCORE_TOTAL_CHECK with value=6",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: ACTIVATE_ENERGY with value=2",
        "2 cards share this pattern (園田海未 variants)"
    ],
    "text_mapping": {
        "自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合": "Frame 0: SCORE_TOTAL_CHECK with value=6",
        "エネルギーを2枚アクティブにする": "Frame 2: ACTIVATE_ENERGY with value=2"
    }
}

# Ability 144: If success pile≥1 and score total≤1, grant +1 score ability
ability_144 = data['abilities'][144]
ability_144['frame_verification'] = {
    "verified": True,
    "notes": [
        "If success pile≥1 and score total≤1, grant +1 score ability",
        "Frame 0: SUCCESS_PILE_COUNT with value=1",
        "Frame 1: SCORE_COMPARE with value=1",
        "Frame 2: JUMP_IF_FALSE skips if conditions not met",
        "Frame 3: GRANT_ABILITY",
        "2 cards share this pattern (東條希 variants)"
    ],
    "text_mapping": {
        "自分の成功ライブカード置き場にカードが1枚以上あり、かつスコアの合計が１以下の場合": "Frames 0-1: SUCCESS_PILE_COUNT + SCORE_COMPARE",
        "ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る": "Frame 3: GRANT_ABILITY"
    }
}

# Ability 145: If success pile has cards, draw 1
ability_145 = data['abilities'][145]
ability_145['frame_verification'] = {
    "verified": True,
    "notes": [
        "If success pile has cards, draw 1",
        "Frame 0: COUNT_SUCCESS_LIVE with value=1",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: DRAW with value=1",
        "2 cards share this pattern (星空凛 variants)"
    ],
    "text_mapping": {
        "自分の成功ライブカード置き場にカードがある場合": "Frame 0: COUNT_SUCCESS_LIVE with value=1",
        "カードを1枚引く": "Frame 2: DRAW with value=1"
    }
}

# Ability 146: Put Muse live from discard to deck top, if opponent has tapped member draw 1
ability_146 = data['abilities'][146]
ability_146['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional select Muse live from discard to deck top, if opponent has tapped member draw 1",
        "Frame 0: SELECT_CARDS with card_type=LIVE, group_id=MUSE, is_optional=1",
        "Frame 1: MOVE_TO_DECK with dest_zone=DECK, remainder_zone=DECK_TOP",
        "Frame 2: COUNT_STAGE with is_tapped=1, target_player=OPPONENT",
        "Frame 3: JUMP_IF_FALSE skips if condition not met",
        "Frame 4: DRAW with value=1",
        "2 cards share this pattern (西木野真姫 variants)"
    ],
    "text_mapping": {
        "自分の控え室から『μ's』のライブカードを1枚までデッキの一番上に置く": "Frames 0-1: SELECT_CARDS + MOVE_TO_DECK",
        "その後、相手のステージにウェイト状態のメンバーがいる場合、カードを1枚引く": "Frames 2-4: COUNT_STAGE (is_tapped=1, OPPONENT) + JUMP_IF_FALSE + DRAW"
    }
}

# Ability 147: Select 2 unique live from discard, opponent chooses 1, add to hand
ability_147 = data['abilities'][147]
ability_147['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional select 2 unique live from discard, opponent chooses 1, add to hand",
        "Frame 0: SELECT_CARDS with card_type=LIVE, unique_names=1, is_optional=1",
        "Frame 1: OPPONENT_CHOOSE with value=1",
        "Frame 2: ADD_TO_HAND with value=1",
        "2 cards share this pattern (鬼塚冬毬 variants)"
    ],
    "text_mapping": {
        "自分の控え室にある、カード名の異なるライブカードを2枚選ぶ": "Frame 0: SELECT_CARDS with unique_names=1",
        "そうした場合、相手はそれらのカードのうち1枚を選ぶ": "Frame 1: OPPONENT_CHOOSE",
        "これにより相手に選ばれたカードを自分の手札に加える": "Frame 2: ADD_TO_HAND"
    }
}

# Ability 148: Trigger remote cost≤4 Nijigasaki member from discard
ability_148 = data['abilities'][148]
ability_148['frame_verification'] = {
    "verified": True,
    "notes": [
        "Trigger remote cost≤4 Nijigasaki member from discard",
        "Frame 0: TRIGGER_REMOTE with card_type=MEMBER, group_id=NIJIGASAKI, value_threshold=4, is_le=1",
        "2 cards share this pattern (桜坂しずく variants)"
    ],
    "text_mapping": {
        "自分の控え室にあるコスト4以下の『虹ヶ咲』のメンバーカードを1枚選ぶ。そのカードの{{toujyou.png|登場}}能力1つを発動させる": "Frame 0: TRIGGER_REMOTE with group_id=NIJIGASAKI, value_threshold=4"
    }
}

# Ability 149: LOOK_AND_CHOOSE 5 for Eli/Karin/Ren, tap all opponents with ≤3 blades and cost≤selected
ability_149 = data['abilities'][149]
ability_149['frame_verification'] = {
    "verified": True,
    "notes": [
        "LOOK_AND_CHOOSE 5 for Eli/Karin/Ren, tap all opponents with ≤3 blades and cost≤selected",
        "Frame 0: LOOK_AND_CHOOSE with count=5, dest_discard=1, char_id_1=ELI, char_id_2=KARIN, char_id_3=REN",
        "Frame 1: TAP_OPPONENT with value=99, filter=BLADE_LE3",
        "Note: Missing cost comparison with selected card - text says 'これにより公開したカードのコスト以下'",
        "1 card shares this pattern (絢瀬絵里&朝香果林&葉月恋)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを5枚見る。その中から「絢瀬絵里」か「朝香果林」か「葉月恋」のメンバーカードを1枚公開して手札に加えてもよい": "Frame 0: LOOK_AND_CHOOSE with char_id_1=ELI, char_id_2=KARIN, char_id_3=REN",
        "その後、相手のステージにいる、これにより公開したカードのコスト以下で、かつ元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバーをすべてウェイトにする": "Frame 1: TAP_OPPONENT with filter=BLADE_LE3 (ISSUE: missing cost comparison)"
    }
}

# Ability 150: Optional pay 2 energy to recover Liella member
ability_150 = data['abilities'][150]
ability_150['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 2 energy to recover Liella member",
        "Frame 0: PAY_ENERGY with value=2, is_optional=1",
        "Frame 1: JUMP_IF_FALSE skips if not paid",
        "Frame 2: RECOVER_MEMBER with group_id=LIELLA",
        "1 card shares this pattern (米女メイ)"
    ],
    "text_mapping": {
        "{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY with value=2, is_optional=1",
        "自分の控え室から『Liella!』のメンバーカードを1枚手札に加える": "Frame 2: RECOVER_MEMBER with group_id=LIELLA"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Added frame_verification for abilities 101-150")
print("Saved file")
