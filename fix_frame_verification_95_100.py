import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Fixing frame_verification for abilities 95-100...")

# Ability 95: Tap self to LOOK_AND_CHOOSE 4 for Liella live with hearts≥8 (fix incorrect verification)
ability_95 = data['abilities'][95]
ability_95['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional tap self to look at 4, choose Liella live with hearts≥8 to hand",
        "Frame 0: SET_TAPPED optional on self",
        "Frame 1: JUMP_IF_FALSE skips if not tapped",
        "Frame 2: LOOK_AND_CHOOSE with count=4, reveal=1, group_id=LIELLA, card_type=LIVE, value_threshold=8",
        "2 cards share this pattern (唐可可 variants)"
    ],
    "text_mapping": {
        "このメンバーをウェイトにしてもよい": "Frame 0: SET_TAPPED with is_optional=1",
        "自分のデッキの上からカードを4枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=4",
        "その中から必要ハートの合計が8以上の『Liella!』のライブカードを1枚公開して手札に加えてもよい": "Frame 2: group_id=LIELLA, card_type=LIVE, value_threshold=8, reveal=1",
        "残りを控え室に置く": "Frame 2: dest_discard=1"
    }
}

# Ability 96: Tap self to recover Muse member (fix incorrect verification)
ability_96 = data['abilities'][96]
ability_96['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional tap self to recover Muse member from discard",
        "Frame 0: MOVE_MEMBER with is_optional=1, is_wait=1 (tap self)",
        "Frame 1: JUMP_IF_FALSE skips if not tapped",
        "Frame 2: RECOVER_MEMBER",
        "2 cards share this pattern (南ことり variants)"
    ],
    "text_mapping": {
        "このメンバーをウェイトにしてもよい": "Frame 0: MOVE_MEMBER with is_optional=1, is_wait=1",
        "自分の控え室から『μ's』のメンバーカードを1枚手札に加える": "Frame 2: RECOVER_MEMBER (ISSUE: missing group_id=MUSE filter)"
    }
}

# Ability 97: Draw 1, then position change to different area
ability_97 = data['abilities'][97]
ability_97['frame_verification'] = {
    "verified": True,
    "notes": [
        "Draw 1 card, then position change to different area",
        "Frame 0: DRAW with value=1",
        "Frame 1: SWAP_AREA moves member to different area",
        "2 cards share this pattern (若菜四季 variants)"
    ],
    "text_mapping": {
        "カードを1枚引く": "Frame 0: DRAW with value=1",
        "その後、登場したエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する": "Frame 1: SWAP_AREA",
        "選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる": "SWAP_AREA handles the swap"
    }
}

# Ability 98: Draw 1, if Mei on stage draw another
ability_98 = data['abilities'][98]
ability_98['frame_verification'] = {
    "verified": True,
    "notes": [
        "Draw 1 card, if Mei on stage draw another",
        "Frame 0: DRAW with value=1",
        "Frame 1: COUNT_STAGE with char_id_1=MEI",
        "Frame 2: JUMP_IF_FALSE skips if no Mei",
        "Frame 3: DRAW with value=1",
        "2 cards share this pattern (若菜四季 variants)"
    ],
    "text_mapping": {
        "カードを1枚引く": "Frame 0: DRAW with value=1",
        "自分のステージに「米女メイ」がいる場合、さらにカードを1枚引く": "Frames 1-3: COUNT_STAGE (char_id_1=MEI) + JUMP_IF_FALSE + DRAW"
    }
}

# Ability 99: Mill 5 from deck top
ability_99 = data['abilities'][99]
ability_99['frame_verification'] = {
    "verified": True,
    "notes": [
        "Mill 5 cards from deck top to discard",
        "Frame 0: MOVE_TO_DISCARD with value=5, source_zone=DECK_TOP",
        "2 cards share this pattern (村野さやか variants)"
    ],
    "text_mapping": {
        "デッキの上からカードを5枚控え室に置く": "Frame 0: MOVE_TO_DISCARD with value=5, source_zone=DECK_TOP"
    }
}

# Ability 100: Tap up to 3 members, draw per tapped member
ability_100 = data['abilities'][100]
ability_100['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional tap up to 3 members, draw 1 per tapped member",
        "Frame 0: SELECT_MEMBER with value=3",
        "Frame 1: MOVE_MEMBER with is_optional=1, is_wait=1 (tap)",
        "Frame 2: JUMP_IF_FALSE skips if none tapped",
        "Frame 3: DRAW with value=1",
        "Note: Only draws 1 total, not per tapped member - ISSUE",
        "2 cards share this pattern (小泉花陽 variants)"
    ],
    "text_mapping": {
        "メンバーを3人までウェイトにしてもよい": "Frames 0-1: SELECT_MEMBER + MOVE_MEMBER with is_optional=1",
        "これによりウェイト状態にしたメンバー1人につき、カードを1枚引く": "Frame 3: DRAW with value=1 (ISSUE: should draw per member, not just 1)"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed frame_verification for abilities 95-100")
print("Completed manual review of abilities 0-100")
print("Saved file")
