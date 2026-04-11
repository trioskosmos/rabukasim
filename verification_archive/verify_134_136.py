import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying abilities 134-136...")

# Ability 134
ability_134 = data['abilities'][134]
ability_134['frame_verification'] = {
    "verified": True,
    "notes": [
        "Look at 2 cards, optionally reveal and add Karin member to hand, discard rest",
        "Frame 0: LOOK_AND_CHOOSE with count=2, reveal=1, dest_discard=1, char_id_1=KARIN",
        "2 cards share this pattern (朝香果林 variants)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを2枚見る": "Frame 0: LOOK_AND_CHOOSE value.count=2",
        "その中から「朝香果林」のメンバーカードを1枚公開して手札に加えてもよい": "Frame 0: char_id_1=KARIN, reveal=1, is_optional=1",
        "残りを控え室に置く": "Frame 0: dest_discard=1, remainder_zone=DISCARD"
    }
}

# Ability 135
ability_135 = data['abilities'][135]
ability_135['frame_verification'] = {
    "verified": True,
    "notes": [
        "Look at 2 cards, optionally reveal and add Kanata member to hand, discard rest",
        "Frame 0: LOOK_AND_CHOOSE with count=2, reveal=1, dest_discard=1, char_id_1=KANATA",
        "2 cards share this pattern (近江彼方 variants)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを2枚見る": "Frame 0: LOOK_AND_CHOOSE value.count=2",
        "その中から「近江彼方」のメンバーカードを1枚公開して手札に加えてもよい": "Frame 0: char_id_1=KANATA, reveal=1, is_optional=1",
        "残りを控え室に置く": "Frame 0: dest_discard=1, remainder_zone=DISCARD"
    }
}

# Ability 136
ability_136 = data['abilities'][136]
ability_136['frame_verification'] = {
    "verified": True,
    "notes": [
        "Look at 2 cards, optionally reveal and add Lanzhu member to hand, discard rest",
        "Frame 0: LOOK_AND_CHOOSE with count=2, reveal=1, dest_discard=1, char_id_1=LANZHU",
        "2 cards share this pattern (鐘嵐珠 variants)"
    ],
    "text_mapping": {
        "自分のデッキの上からカードを2枚見る": "Frame 0: LOOK_AND_CHOOSE value.count=2",
        "その中から「鐘嵐珠」のメンバーカードを1枚公開して手札に加えてもよい": "Frame 0: char_id_1=LANZHU, reveal=1, is_optional=1",
        "残りを控え室に置く": "Frame 0: dest_discard=1, remainder_zone=DISCARD"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified abilities 134-136")
print("Saved file")
