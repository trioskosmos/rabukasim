import json

with open('../data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

# Find the ability at index 142 (SCORE_TOTAL_CHECK + LOOK_AND_CHOOSE for μ's)
for i, ability in enumerate(abilities):
    if i == 142:
        print(f"Found ability at index {i}")
        print(f"Primary text: {ability.get('primary_text_jp', 'NO_TEXT')[:100]}")
        
        # Fix frame data: add group_id: MUSE to LOOK_AND_CHOOSE frame
        frames = ability.get('frames', [])
        for frame in frames:
            if frame.get('op') == 'LOOK_AND_CHOOSE':
                attr = frame.get('attr', {})
                attr['group_id'] = 'MUSE'
                print(f"Added group_id: MUSE to frame {frame.get('frame_index')}")
        
        # Update frame_verification
        ability['frame_verification'] = {
            "verified": True,
            "notes": [
                "ON_PLAY: If total score of success live cards is 3 or more, look at 5 cards from top of deck, optionally reveal and add 1 μ's member card to hand, discard rest.",
                "Frame 0: SCORE_TOTAL_CHECK with value=3, target_slot=STAGE_0, comparison=GE - checks if total score is >= 3",
                "Frame 1: JUMP_IF_FALSE with value=1 - skips effect if condition not met",
                "Frame 2: LOOK_AND_CHOOSE with count=5, reveal=1, dest_discard=1, group_enabled=1, group_id=MUSE, target_slot=HAND, remainder_zone=DISCARD, source_zone=DECK_TOP - looks at 5 cards, optionally reveals and adds μ's member card to hand, discards rest",
                "Frame 3: RETURN",
                "2 cards share this pattern (西木野真姫 variants)"
            ],
            "text_mapping": {
                "自分の成功ライブカード置き場にあるカードのスコアの合計が３以上の場合": "Frame 0: SCORE_TOTAL_CHECK with value=3, comparison=GE",
                "自分のデッキの上からカードを5枚見る": "Frame 2: LOOK_AND_CHOOSE with count=5, source_zone=DECK_TOP",
                "その中から『μ's』のメンバーカードを1枚公開して手札に加えてもよい": "Frame 2: LOOK_AND_CHOOSE with reveal=1, group_enabled=1, group_id=MUSE, is_optional=1, target_slot=HAND",
                "残りを控え室に置く": "Frame 2: LOOK_AND_CHOOSE with remainder_zone=DISCARD"
            }
        }
        print(f"Updated frame_verification for ability at index {i}")
        break

# Write back
with open('../data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done")
