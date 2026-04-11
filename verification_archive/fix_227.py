import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Fixing ability 227...")

# Ability 227 - fix frames to match auto-trigger text
ability_227 = data['abilities'][227]
ability_227['frames'] = [
    {
        "op": "NOP",
        "frame_index": 0,
        "params": {
            "raw_cond": "OPPONENT_MEMBER_TAPPED_BY_YOUR_EFFECT_COST_LE4"
        },
        "attr": {
            "once_per_turn": 1
        }
    },
    {
        "op": "JUMP_IF_FALSE",
        "frame_index": 1,
        "value": 1
    },
    {
        "op": "DRAW",
        "frame_index": 2,
        "value": 1,
        "slot": {
            "target_slot": "CONTEXT"
        }
    },
    {
        "op": "RETURN",
        "frame_index": 3
    }
]
ability_227['frame_verification'] = {
    "verified": True,
    "notes": [
        "Auto trigger: when opponent cost≤4 member becomes tapped by your effect, draw 1",
        "Fixed: Changed from wrong IS_CENTER/MOVE_MEMBER frames to correct auto-trigger frames",
        "Frame 0: NOP with raw_cond=OPPONENT_MEMBER_TAPPED_BY_YOUR_EFFECT_COST_LE4, once_per_turn=1",
        "Frame 2: DRAW",
        "2 cards share this pattern"
    ],
    "text_mapping": {
        "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のカードの効果によって、相手のステージにいるアクティブ状態のコスト4以下のメンバーがウェイト状態になったとき": "Frame 0: NOP with raw_cond",
        "カードを1枚引く": "Frame 2: DRAW"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed ability 227")
print("Saved file")
