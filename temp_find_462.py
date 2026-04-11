import json

with open('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('abilities', [])

for i, ab in enumerate(abilities):
    cards = ab.get('card_refs', [])
    for card in cards:
        if card.get('card_id') == 462:
            print(f'Ability #{i}: card_id 462, ability_index={card.get("ability_index")}')
