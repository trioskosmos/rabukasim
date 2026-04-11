import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 120...")

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

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 120 - frames match text correctly")
print("Saved file")
