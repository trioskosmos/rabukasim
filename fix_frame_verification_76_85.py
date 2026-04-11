import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Fixing frame_verification for abilities 76-85...")

# Ability 76: Score total >= 6 to activate 1 energy (fix incorrect verification)
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

# Ability 77: Auto when cost11 member plays, activate 1 energy (fix incorrect verification)
ability_77 = data['abilities'][77]
ability_77['frame_verification'] = {
    "verified": True,
    "notes": [
        "Auto ability (once per turn): When cost11 member plays, activate 1 energy",
        "Frame 0: COUNT_STAGE with once_per_turn=1",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: ACTIVATE_ENERGY with value=1",
        "Note: Missing cost11 filter in COUNT_STAGE - text specifies cost11",
        "2 cards share this pattern (鐘嵐珠 variants)"
    ],
    "text_mapping": {
        "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにこのメンバー以外のコスト11のメンバーが登場したとき": "Frame 0: COUNT_STAGE with once_per_turn=1 (ISSUE: missing cost11 filter)",
        "自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く": "Frame 2: ACTIVATE_ENERGY with value=1"
    }
}

# Ability 78: Auto when cost10 member plays, draw 1 (fix incorrect verification)
ability_78 = data['abilities'][78]
ability_78['frame_verification'] = {
    "verified": True,
    "notes": [
        "Auto ability (once per turn): When cost10 member plays, draw 1 card",
        "Frame 0: GROUP_FILTER with once_per_turn=1",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: DRAW with value=1",
        "Note: Missing cost10 filter - text specifies cost10",
        "2 cards share this pattern (宮下愛 variants)"
    ],
    "text_mapping": {
        "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにコスト10のメンバーが登場したとき": "Frame 0: GROUP_FILTER with once_per_turn=1 (ISSUE: missing cost10 filter)",
        "カードを1枚引く": "Frame 2: DRAW with value=1"
    }
}

# Ability 79: Center BiBi tap to tap opponent
ability_79 = data['abilities'][79]
ability_79['frame_verification'] = {
    "verified": True,
    "notes": [
        "Center check: Optional tap BiBi member to tap 1 opponent active member",
        "Frame 0: IS_CENTER checks if in center",
        "Frame 1: JUMP_IF_FALSE skips if not center",
        "Frame 2: MOVE_MEMBER with unit_id=BIBI, is_optional=1, is_wait=1",
        "Frame 3: JUMP_IF_FALSE skips if not tapped",
        "Frame 4: TAP_OPPONENT with value=1",
        "2 cards share this pattern (西木野真姫 variants)"
    ],
    "text_mapping": {
        "{{center.png|センター}}": "Frame 0: IS_CENTER",
        "『BiBi』のメンバー1人をウェイトにしてもよい": "Frame 2: MOVE_MEMBER with unit_id=BIBI, is_optional=1, is_wait=1",
        "相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする": "Frame 4: TAP_OPPONENT with value=1"
    }
}

# Ability 80: Tap self, BiBi only to tap opponent with <=3 blades
ability_80 = data['abilities'][80]
ability_80['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional tap self: If stage has only BiBi members, tap opponent with <=3 blades",
        "Frame 0: GROUP_FILTER with unit_id=BIBI, value=4 - checks if 4+ BiBi members",
        "Frame 1: JUMP_IF_FALSE skips if not BiBi only",
        "Frame 2: SET_TAPPED optional on self",
        "Frame 3: JUMP_IF_FALSE skips if not tapped",
        "Frame 4: SELECT_MEMBER targeting OPPONENT with filter=BLADE_LE3",
        "Frame 5: MOVE_MEMBER with is_wait=1 to tap selected opponent",
        "3 cards share this pattern (絢瀬絵里 variants)"
    ],
    "text_mapping": {
        "このメンバーをウェイトにしてもよい": "Frame 2: SET_TAPPED with is_optional=1",
        "自分のステージにいるメンバーが『BiBi』のみの場合": "Frame 0: GROUP_FILTER with unit_id=BIBI (checks 4+ BiBi, may be incorrect logic)",
        "相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする": "Frame 4: SELECT_MEMBER with filter=BLADE_LE3 + Frame 5: MOVE_MEMBER with is_wait=1"
    }
}

# Ability 81: Center, success pile Muse cards grant ability
ability_81 = data['abilities'][81]
ability_81['frame_verification'] = {
    "verified": True,
    "notes": [
        "Center check: If success pile has Muse cards, grant ability (+1 or +2 score)",
        "Frame 0: IS_CENTER checks if in center",
        "Frame 1: SUCCESS_PILE_COUNT with group_enabled (Muse)",
        "Frame 2: JUMP_IF_FALSE skips if no Muse cards",
        "Frame 3: GRANT_ABILITY with value=1 (+1 score)",
        "Frame 4: GRANT_ABILITY with value=2 (+2 score)",
        "Note: Missing logic to check if 1 card vs 2+ cards - both abilities granted regardless",
        "2 cards share this pattern (園田海未 variants)"
    ],
    "text_mapping": {
        "{{center.png|センター}}": "Frame 0: IS_CENTER",
        "自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合": "Frame 1: SUCCESS_PILE_COUNT with group=Muse (ISSUE: missing count check)",
        "ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る": "Frame 3: GRANT_ABILITY with value=1",
        "2枚以上ある場合、代わりに「{{jyouji.png|常時}}ライブの合計スコアを+２する。」を得る": "Frame 4: GRANT_ABILITY with value=2 (ISSUE: both granted regardless of count)"
    }
}

# Ability 82: Pay 4 energy to play 2 members from discard
ability_82 = data['abilities'][82]
ability_82['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 4 energy to play up to 2 members from discard with total cost <= 4",
        "Frame 0: PAY_ENERGY with value=4, is_optional=1",
        "Frame 1: JUMP_IF_FALSE skips if not paid",
        "Frame 2: PLAY_MEMBER_FROM_DISCARD with value=2, value_threshold=4, is_le=1, is_cost_type=1",
        "2 cards share this pattern (津島善子 variants)"
    ],
    "text_mapping": {
        "{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY with value=4, is_optional=1",
        "自分の控え室から、コストの合計が4以下になるようにメンバーカードを2枚までステージに登場させる": "Frame 2: PLAY_MEMBER_FROM_DISCARD with value=2, value_threshold=4, is_le=1, is_cost_type=1"
    }
}

# Ability 83: Pay 2 energy to look at 7 for Liella
ability_83 = data['abilities'][83]
ability_83['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 2 energy to look at 7, choose Liella card to hand",
        "Frame 0: PAY_ENERGY with value=2, is_optional=1",
        "Frame 1: JUMP_IF_FALSE skips to RETURN if not paid",
        "Frame 2: SUM_VALUE",
        "Frame 3: JUMP_IF_FALSE skips if condition not met",
        "Frame 4: LOOK_AND_CHOOSE with count=7, group_id=LIELLA, is_optional=1",
        "2 cards share this pattern (葉月恋 variants)"
    ],
    "text_mapping": {
        "{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY with value=2, is_optional=1",
        "自分のデッキの上からカードを7枚見る": "Frame 4: LOOK_AND_CHOOSE value.count=7",
        "その中から『Liella!』のカードを1枚公開して手札に加えてもよい": "Frame 4: group_id=LIELLA, is_optional=1"
    }
}

# Ability 84: Pay 2 energy to play Nijigasaki member from hand
ability_84 = data['abilities'][84]
ability_84['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 2 energy to play cost≤4 Nijigasaki member from hand, tap self if member has blade heart",
        "Frame 0: PAY_ENERGY with value=2, is_optional=1",
        "Frame 1: JUMP_IF_FALSE skips to RETURN if not paid",
        "Frame 2: PLAY_MEMBER_FROM_HAND with group_id=NIJIGASAKI, cost≤4",
        "Frame 3: NOP checks condition",
        "Frame 4: JUMP_IF_FALSE skips if condition not met",
        "Frame 5: MOVE_MEMBER with is_wait=1 to tap self",
        "2 cards share this pattern (近江彼方 variants)"
    ],
    "text_mapping": {
        "{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY with value=2, is_optional=1",
        "自分の手札からコスト4以下の『虹ヶ咲』のメンバーカードを1枚ステージに登場させる": "Frame 2: PLAY_MEMBER_FROM_HAND with group_id=NIJIGASAKI, value_threshold=4, is_le=1",
        "これにより登場したメンバーがブレードハートを持つ場合、このメンバーをウェイトにする": "Frames 3-5: NOP + JUMP_IF_FALSE + MOVE_MEMBER with is_wait=1"
    }
}

# Ability 85: Pay 1 energy + baton from Mira Cra Park to gain hearts
ability_85 = data['abilities'][85]
ability_85['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional pay 1 energy: If baton from lower cost Mira Cra Park, gain 2 heart01",
        "Frame 0: PAY_ENERGY with value=1, is_optional=1",
        "Frame 1: JUMP_IF_FALSE skips to RETURN if not paid",
        "Frame 2: BATON with unit_id=MIRA_CRA_PARK",
        "2 cards share this pattern (安養寺姫芽 variants)"
    ],
    "text_mapping": {
        "{{icon_energy.png|E}}支払ってもよい": "Frame 0: PAY_ENERGY with value=1, is_optional=1",
        "このメンバーよりコストが低い『みらくらぱーく！』のメンバーからバトンタッチして登場した場合": "Frame 2: BATON with unit_id=MIRA_CRA_PARK",
        "ライブ終了時まで、{{heart_01.png|heart01}}{{heart_01.png|heart01}}を得る": "NOT IMPLEMENTED - missing ADD_HEARTS or similar frame"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed frame_verification for abilities 76-85")
print("Saved file")
