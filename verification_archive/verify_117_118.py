import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 117-118...")

# Ability 117
ability_117 = data['abilities'][117]
ability_117['frame_verification'] = {
    "verified": True,
    "notes": [
        "If opponent hand count ≥2 more than self, recover live",
        "Frame 0: SUM_VALUE with value=2",
        "Frame 1: JUMP_IF_FALSE skips if condition not met",
        "Frame 2: RECOVER_LIVE with value=1",
        "2 cards share this pattern (高海千歌 variants)"
    ],
    "text_mapping": {
        "相手の手札の枚数が自分より2枚以上多い場合": "Frame 0: SUM_VALUE with value=2",
        "自分の控え室からライブカードを1枚手札に加える": "Frame 2: RECOVER_LIVE with value=1"
    }
}

# Ability 118
ability_118 = data['abilities'][118]
ability_118['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: TAP_OPPONENT missing is_tapped=0 filter for 'アクティブ状態' (active state)",
        "Text specifies tapping active members, but frame doesn't filter for untapped members"
    ],
    "text_mapping": {
        "相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする": "Frame 0: TAP_OPPONENT with value=1 (ISSUE: missing is_tapped=0 filter)"
    },
    "required_frames": [
        "TAP_OPPONENT should have is_tapped=0 to select only active members"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 117-118")
print("Saved file")
