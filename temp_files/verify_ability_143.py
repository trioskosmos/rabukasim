import json

with open('../data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

# Find the ability at index 143 (SCORE_TOTAL_CHECK + ACTIVATE_ENERGY)
for i, ability in enumerate(abilities):
    if i == 143:
        print(f"Found ability at index {i}")
        print(f"Primary text: {ability.get('primary_text_jp', 'NO_TEXT')[:100]}")
        
        # Update frame_verification
        ability['frame_verification'] = {
            "verified": True,
            "notes": [
                "ON_PLAY: If total score of success live cards is 6 or more, activate 2 energy cards.",
                "Frame 0: SCORE_TOTAL_CHECK with value=6, target_slot=STAGE_0, comparison=GE - checks if total score is >= 6",
                "Frame 1: JUMP_IF_FALSE with value=1 - skips effect if condition not met",
                "Frame 2: ACTIVATE_ENERGY with value=2, target_slot=CONTEXT - activates 2 energy cards",
                "Frame 3: RETURN",
                "2 cards share this pattern (園田海未 variants)"
            ],
            "text_mapping": {
                "自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合": "Frame 0: SCORE_TOTAL_CHECK with value=6, comparison=GE",
                "エネルギーを2枚アクティブにする": "Frame 2: ACTIVATE_ENERGY with value=2"
            }
        }
        print(f"Updated frame_verification for ability at index {i}")
        break

# Write back
with open('../data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done")
