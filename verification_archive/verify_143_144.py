import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 143-144...")

# Ability 143
ability_143 = data['abilities'][143]
ability_143['frame_verification'] = {
    "verified": True,
    "notes": [
        "If success live score total ≥6, activate 2 energy",
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

# Ability 144
ability_144 = data['abilities'][144]
ability_144['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 1: SCORE_COMPARE uses comparison=GE but text says 'スコアの合計が１以下' (score total ≤1)",
        "Comparison should be LE not GE"
    ],
    "text_mapping": {
        "自分の成功ライブカード置き場にカードが1枚以上あり": "Frame 0: SUCCESS_PILE_COUNT with value=1",
        "かつスコアの合計が１以下の場合": "Frame 1: SCORE_COMPARE with value=1 (ISSUE: comparison should be LE, not GE)",
        "ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る": "Frame 3: GRANT_ABILITY"
    },
    "required_frames": [
        "SCORE_COMPARE should have comparison=LE for '1以下'"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 143-144")
print("Saved file")
