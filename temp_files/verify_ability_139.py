import json

with open('../data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

# Find the ability at index 139 (the one that was just fixed)
# and the next ability (index 140) which is the LOOK_AND_CHOOSE cost 11+ ability
for i, ability in enumerate(abilities):
    if i == 140:
        # This is the LOOK_AND_CHOOSE cost 11+ ability
        print(f"Found ability at index {i}")
        print(f"Primary text: {ability.get('primary_text_jp', 'NO_TEXT')[:100]}")
        
        # Update frame_verification
        ability['frame_verification'] = {
            "verified": True,
            "notes": [
                "ON_PLAY: Look at 3 cards from top of deck, optionally reveal and add 1 card with cost 11+ to hand, discard rest.",
                "Frame 0: LOOK_AND_CHOOSE with count=3, reveal=1, dest_discard=1, value_enabled=1, value_threshold=11, is_cost_type=1, is_optional=1, target_slot=HAND, remainder_zone=DISCARD, source_zone=DECK_TOP - looks at 3 cards, optionally reveals and adds cost 11+ card to hand, discards rest",
                "Frame 1: RETURN",
                "2 cards share this pattern (桜坂小雫 variants)"
            ],
            "text_mapping": {
                "自分のデッキの上からカードを3枚見る": "Frame 0: LOOK_AND_CHOOSE with count=3, source_zone=DECK_TOP",
                "その中からコスト11以上のカードを1枚公開して手札に加えてもよい": "Frame 0: LOOK_AND_CHOOSE with reveal=1, value_enabled=1, value_threshold=11, is_cost_type=1, is_optional=1, target_slot=HAND",
                "残りを控え室に置く": "Frame 0: LOOK_AND_CHOOSE with remainder_zone=DISCARD"
            }
        }
        print(f"Updated frame_verification for ability at index {i}")
        break

# Write back
with open('../data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done")
