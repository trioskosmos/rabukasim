import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 145-150...")

# Ability 145
ability_145 = data['abilities'][145]
ability_145['frame_verification'] = {
    "verified": True,
    "notes": [
        "If success live pile has cards, draw 1",
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

# Ability 146
ability_146 = data['abilities'][146]
ability_146['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional put 1 Muse live from discard to deck top, then if opponent has tapped member, draw 1",
        "Frame 0: SELECT_CARDS with group_id=MUSE",
        "Frame 1: MOVE_TO_DECK to DECK_TOP",
        "Frame 2: COUNT_STAGE for opponent tapped",
        "Frame 3: JUMP_IF_FALSE",
        "Frame 4: DRAW",
        "2 cards share this pattern (西木野真姫 variants)"
    ],
    "text_mapping": {
        "自分の控え室から『μ's』のライブカードを1枚までデッキの一番上に置く": "Frames 0-1: SELECT_CARDS + MOVE_TO_DECK",
        "その後、相手のステージにウェイト状態のメンバーがいる場合、カードを1枚引く": "Frames 2-4: COUNT_STAGE + JUMP_IF_FALSE + DRAW"
    }
}

# Ability 147
ability_147 = data['abilities'][147]
ability_147['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional select 2 unique live cards from discard, opponent chooses 1, add to hand",
        "Frame 0: SELECT_CARDS with unique_names=1",
        "Frame 1: OPPONENT_CHOOSE",
        "Frame 2: ADD_TO_HAND",
        "2 cards share this pattern (鬼塚冬毬 variants)"
    ],
    "text_mapping": {
        "自分の控え室にある、カード名の異なるライブカードを2枚選ぶ": "Frame 0: SELECT_CARDS with unique_names=1",
        "そうした場合、相手はそれらのカードのうち1枚を選ぶ": "Frame 1: OPPONENT_CHOOSE",
        "これにより相手に選ばれたカードを自分の手札に加える": "Frame 2: ADD_TO_HAND"
    }
}

# Ability 148
ability_148 = data['abilities'][148]
ability_148['frame_verification'] = {
    "verified": True,
    "notes": [
        "Select 1 cost≤4 Nijigasaki member from discard and trigger its on-play ability",
        "Frame 0: TRIGGER_REMOTE with cost≤4, group_id=NIJIGASAKI",
        "2 cards share this pattern (桜坂しずく variants)"
    ],
    "text_mapping": {
        "自分の控え室にあるコスト4以下の『虹ヶ咲』のメンバーカードを1枚選ぶ": "Frame 0: TRIGGER_REMOTE with cost≤4, group_id=NIJIGASAKI",
        "そのカードの{{toujyou.png|登場}}能力1つを発動させる": "Frame 0: TRIGGER_REMOTE (triggers ability)"
    }
}

# Ability 149
ability_149 = data['abilities'][149]
ability_149['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: LOOK_AND_CHOOSE missing reveal=1 for '公開して' (reveal)",
        "Frame 1: TAP_OPPONENT missing cost filter - text says 'これにより公開したカードのコスト以下で' (cost ≤ revealed card's cost)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを5枚見る": "Frame 0: LOOK_AND_CHOOSE value.count=5",
        "その中から「絢瀬絵里」か「朝香果林」か「葉月恋」のメンバーカードを1枚公開して手札に加えてもよい": "Frame 0: char_id_1=ELI, char_id_2=KARIN, char_id_3=REN (ISSUE: missing reveal=1)",
        "残りを控え室に置く": "Frame 0: dest_discard=1, remainder_zone=DISCARD",
        "その後、相手のステージにいる、これにより公開したカードのコスト以下で、かつ元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバーをすべてウェイトにする": "Frame 1: TAP_OPPONENT (ISSUE: missing cost filter)"
    },
    "required_frames": [
        "LOOK_AND_CHOOSE should have reveal=1",
        "TAP_OPPONENT should have cost filter based on revealed card's cost"
    ]
}

# Ability 150
ability_150 = data['abilities'][150]
ability_150['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 6: LOOK_AND_CHOOSE missing dest_discard=1 and remainder_zone=DISCARD",
        "Text says '残りを控え室に置く' (put rest in discard) but frame doesn't handle this"
    ],
    "text_mapping": {
        "{{icon_energy.png|E}}支払ってもよい": "Frame 2: PAY_ENERGY with is_optional=1",
        "自分のエネルギーが9枚以上ある場合": "Frame 0: COUNT_ENERGY with value=9",
        "自分のデッキの上からカードを5枚見る": "Frame 6: LOOK_AND_CHOOSE value.count=5",
        "その中から1枚を手札に加え、残りを控え室に置く": "ISSUE: Frame 6 missing dest_discard=1, remainder_zone=DISCARD"
    },
    "required_frames": [
        "LOOK_AND_CHOOSE should have dest_discard=1, remainder_zone=DISCARD"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 145-150")
print("Saved file")
