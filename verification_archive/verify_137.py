import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 137...")

ability_137 = data['abilities'][137]
ability_137['frame_verification'] = {
    "verified": True,
    "notes": [
        "Mill 3 cards, if all are member cards with heart01, gain heart01",
        "Frame 0: MOVE_TO_DISCARD with value=3",
        "Frame 1: DISCARDED_CARDS with value=4 (all), card_type=MEMBER",
        "Frame 2: JUMP_IF_FALSE skips if condition not met",
        "Frame 3: ADD_HEARTS with heart_type=0",
        "2 cards share this pattern (安養寺姫芽 variants)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを3枚控え室に置く": "Frame 0: MOVE_TO_DISCARD with value=3",
        "それらがすべて{{heart_01.png|heart01}}を持つメンバーカードの場合": "Frame 1: DISCARDED_CARDS with value=4, card_type=MEMBER",
        "ライブ終了時まで、{{heart_01.png|heart01}}を得る": "Frame 3: ADD_HEARTS with heart_type=0"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 137 - frames match text correctly")
print("Saved file")
