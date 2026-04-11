import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 130-132...")

# Ability 130
ability_130 = data['abilities'][130]
ability_130['frame_verification'] = {
    "verified": True,
    "notes": [
        "If other 5yncri5e member on stage, draw 1",
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

# Ability 131
ability_131 = data['abilities'][131]
ability_131['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: COUNT_STAGE missing special_id='Not Self' for 'ほかの' (other than self)",
        "Text says 'ほかの' but frame doesn't exclude self"
    ],
    "text_mapping": {
        "自分のステージにほかの『虹ヶ咲』のメンバーがいる場合": "Frame 0: COUNT_STAGE with group_id=NIJIGASAKI (ISSUE: missing special_id=Not Self)",
        "エネルギーを1枚アクティブにする": "Frame 2: ACTIVATE_ENERGY with value=1"
    },
    "required_frames": [
        "COUNT_STAGE should have special_id=Not Self to exclude self"
    ]
}

# Ability 132
ability_132 = data['abilities'][132]
ability_132['frame_verification'] = {
    "verified": True,
    "notes": [
        "If 2+ unique BiBi members on stage, tap 1 opponent cost≤4",
        "Frame 0: COUNT_GROUP with value=2, unique_names=1, unit_id=BIBI",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: TAP_OPPONENT with cost≤4",
        "2 cards share this pattern (絢瀬絵里 variants)"
    ],
    "text_mapping": {
        "自分のステージに名前の異なる『BiBi』のメンバーが2人以上いる場合": "Frame 0: COUNT_GROUP with unique_names=1, unit_id=BIBI",
        "相手のステージにいるコスト4以下のメンバー1人をウェイトにする": "Frame 2: TAP_OPPONENT with cost≤4"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 130-132")
print("Saved file")
