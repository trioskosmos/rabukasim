import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 140-142...")

# Ability 140
ability_140 = data['abilities'][140]
ability_140['frame_verification'] = {
    "verified": True,
    "notes": [
        "Look at 3 cards, optionally reveal and add cost≥11 card to hand, discard rest",
        "Frame 0: LOOK_AND_CHOOSE with count=3, reveal=1, dest_discard=1, cost≥11",
        "2 cards share this pattern (唐可可 variants)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを3枚見る": "Frame 0: LOOK_AND_CHOOSE value.count=3",
        "その中からコスト11以上のカードを1枚公開して手札に加えてもよい": "Frame 0: value_threshold=11, is_cost_type=1, reveal=1, is_optional=1",
        "残りを控え室に置く": "Frame 0: dest_discard=1, remainder_zone=DISCARD"
    }
}

# Ability 141
ability_141 = data['abilities'][141]
ability_141['frame_verification'] = {
    "verified": True,
    "notes": [
        "If success live score total ≥3, draw 1",
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

# Ability 142
ability_142 = data['abilities'][142]
ability_142['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 2: LOOK_AND_CHOOSE missing reveal=1 for '公開して' (reveal)",
        "Missing group_id=MUSES for '『μ's』' - only has group_enabled=1 without specifying the group"
    ],
    "text_mapping": {
        "自分の成功ライブカード置き場にあるカードのスコアの合計が３以上の場合": "Frame 0: SCORE_TOTAL_CHECK with value=3",
        "自分のデッキの上からカードを5枚見る": "Frame 2: LOOK_AND_CHOOSE value.count=5",
        "その中から『μ's』のメンバーカードを1枚公開して手札に加えてもよい": "Frame 2: group_enabled=1 (ISSUE: missing group_id=MUSES and reveal=1)",
        "残りを控え室に置く": "Frame 2: dest_discard=1, remainder_zone=DISCARD"
    },
    "required_frames": [
        "LOOK_AND_CHOOSE should have group_id=MUSES and reveal=1"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 140-142")
print("Saved file")
