import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 151-153...")

# Ability 151
ability_151 = data['abilities'][151]
ability_151['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: BATON missing char_id_1=SHIORU to exclude '徒町小鈴' (other than Shioru)",
        "Text says '「徒町小鈴」以外' but frame doesn't exclude Shioru"
    ],
    "text_mapping": {
        "「徒町小鈴」以外の『蓮ノ空』のメンバーからバトンタッチして登場した場合": "Frame 0: BATON with group_id=HASUNOSORA (ISSUE: missing char_id_1=SHIORU)",
        "自分の控え室からライブカードを1枚手札に加える": "Frame 2: RECOVER_LIVE with value=1"
    },
    "required_frames": [
        "BATON should have char_id_1=SHIORU to exclude Shioru"
    ]
}

# Ability 152
ability_152 = data['abilities'][152]
ability_152['frame_verification'] = {
    "verified": True,
    "notes": [
        "Optional tap 1 Nijigasaki member, then draw 1 and discard 1 from hand",
        "Frame 0: SELECT_MEMBER with group_id=NIJIGASAKI",
        "Frame 1: MOVE_MEMBER with is_optional=1, is_wait=1",
        "Frame 2: JUMP_IF_FALSE skips if not activated",
        "Frame 3: DRAW with value=1",
        "Frame 4: MOVE_TO_DISCARD from hand"
    ],
    "text_mapping": {
        "『虹ヶ咲』のメンバー1人をウェイトにしてもよい": "Frames 0-1: SELECT_MEMBER + MOVE_MEMBER with is_optional=1, is_wait=1",
        "カードを1枚引き、手札を1枚控え室に置く": "Frames 3-4: DRAW + MOVE_TO_DISCARD"
    }
}

# Ability 153
ability_153 = data['abilities'][153]
ability_153['frame_verification'] = {
    "verified": True,
    "notes": [
        "If other member moved this turn, draw 1",
        "Frame 0: NOP with raw_cond=COUNT_MOVED_STAGE, MIN=1, special_id=Not Self",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: DRAW with value=1"
    ],
    "text_mapping": {
        "このターン、自分のステージにいるほかのメンバーがエリアを移動している場合": "Frame 0: NOP with raw_cond=COUNT_MOVED_STAGE, special_id=Not Self",
        "カードを1枚引く": "Frame 2: DRAW with value=1"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 151-153")
print("Saved file")
