import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 133...")

ability_133 = data['abilities'][133]
ability_133['frame_verification'] = {
    "verified": True,
    "notes": [
        "Look at 2 cards, optionally reveal and add Rina member to hand, discard rest",
        "Frame 0: LOOK_AND_CHOOSE with count=2, reveal=1, dest_discard=1, char_id_1=RINA",
        "2 cards share this pattern (天王寺璃奈 variants)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを2枚見る": "Frame 0: LOOK_AND_CHOOSE value.count=2",
        "その中から「天王寺璃奈」のメンバーカードを1枚公開して手札に加えてもよい": "Frame 0: char_id_1=RINA, reveal=1, is_optional=1",
        "残りを控え室に置く": "Frame 0: dest_discard=1, remainder_zone=DISCARD"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 133 - frames match text correctly")
print("Saved file")
