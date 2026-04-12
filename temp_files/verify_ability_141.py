import json

with open('../data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

# Find the ability at index 141 (SCORE_TOTAL_CHECK draw 1)
for i, ability in enumerate(abilities):
    if i == 141:
        print(f"Found ability at index {i}")
        print(f"Primary text: {ability.get('primary_text_jp', 'NO_TEXT')[:100]}")
        
        # Update frame_verification
        ability['frame_verification'] = {
            "verified": True,
            "notes": [
                "ON_PLAY: If total score of success live cards is 3 or more, draw 1 card.",
                "Frame 0: SCORE_TOTAL_CHECK with value=3, target_slot=STAGE_0, comparison=GE - checks if total score is >= 3",
                "Frame 1: JUMP_IF_FALSE with value=1 - skips effect if condition not met",
                "Frame 2: DRAW with value=1 - draws 1 card",
                "Frame 3: RETURN",
                "2 cards share this pattern (東條希, 西木野真姫 variants)"
            ],
            "text_mapping": {
                "自分の成功ライブカード置き場にあるカードのスコアの合計が３以上の場合": "Frame 0: SCORE_TOTAL_CHECK with value=3, comparison=GE",
                "カードを1枚引く": "Frame 2: DRAW with value=1"
            }
        }
        print(f"Updated frame_verification for ability at index {i}")
        break

# Write back
with open('../data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done")
