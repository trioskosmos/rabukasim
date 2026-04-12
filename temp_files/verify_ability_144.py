import json

with open('../data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

# Find the ability at index 144 (SUCCESS_PILE_COUNT + SCORE_COMPARE + GRANT_ABILITY)
for i, ability in enumerate(abilities):
    if i == 144:
        print(f"Found ability at index {i}")
        print(f"Primary text: {ability.get('primary_text_jp', 'NO_TEXT')[:100]}")
        
        # Update frame_verification - the frame data is correct (comparison=LE is right for "1 or less")
        ability['frame_verification'] = {
            "verified": True,
            "notes": [
                "ON_PLAY: If success live pile has 1+ cards AND total score is 1 or less, grant 'Always: Total live score +1' until live end.",
                "Frame 0: SUCCESS_PILE_COUNT with value=1, target_slot=STAGE_0, comparison=GE - checks if there are 1+ cards in success pile",
                "Frame 1: SCORE_COMPARE with value=1, target_slot=STAGE_0, comparison=LE - checks if total score is <= 1",
                "Frame 2: JUMP_IF_FALSE with value=1 - skips effect if conditions not met",
                "Frame 3: GRANT_ABILITY with value=1, target_slot=CONTEXT - grants the +1 live score ability",
                "Frame 4: RETURN",
                "2 cards share this pattern (東條希 variants)"
            ],
            "text_mapping": {
                "自分の成功ライブカード置き場にカードが1枚以上あり": "Frame 0: SUCCESS_PILE_COUNT with value=1, comparison=GE",
                "かつスコアの合計が１以下の場合": "Frame 1: SCORE_COMPARE with value=1, comparison=LE",
                "ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る": "Frame 3: GRANT_ABILITY with value=1"
            }
        }
        print(f"Updated frame_verification for ability at index {i}")
        break

# Write back
with open('../data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done")
