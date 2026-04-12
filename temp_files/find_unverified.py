import json

with open('../data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

# Find abilities with verified: false
for i, ability in enumerate(abilities):
    frame_verification = ability.get('frame_verification', {})
    if frame_verification.get('verified') == False:
        print(f"Index {i}: {ability.get('primary_text_jp', 'NO_TEXT')[:100]}")
