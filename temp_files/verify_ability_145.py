import json

with open('../data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

# Find the ability at index 145 (COUNT_SUCCESS_LIVE + DRAW)
for i, ability in enumerate(abilities):
    if i == 145:
        print(f"Found ability at index {i}")
        print(f"Primary text: {ability.get('primary_text_jp', 'NO_TEXT')[:100]}")
        
        # Update frame_verification
        ability['frame_verification'] = {
            "verified": True,
            "notes": [
                "ON_PLAY: If there are cards in success live card area, draw 1 card.",
                "Frame 0: COUNT_SUCCESS_LIVE with value=1, target_slot=STAGE_0, comparison=GE - checks if there are 1+ cards in success live area",
                "Frame 1: JUMP_IF_FALSE with value=1 - skips effect if condition not met",
                "Frame 2: DRAW with value=1, target_slot=CONTEXT - draws 1 card",
                "Frame 3: RETURN",
                "2 cards share this pattern (星空凛 variants)"
            ],
            "text_mapping": {
                "自分の成功ライブカード置き場にカードがある場合": "Frame 0: COUNT_SUCCESS_LIVE with value=1, comparison=GE",
                "カードを1枚引く": "Frame 2: DRAW with value=1"
            }
        }
        print(f"Updated frame_verification for ability at index {i}")
        break

# Write back
with open('../data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done")
