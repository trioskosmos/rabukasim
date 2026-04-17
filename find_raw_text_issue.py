"""Find the ability with raw text issue."""

import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['unique_abilities']

# Find ability index 209
if len(abilities) > 209:
    ability = abilities[209]
    print(f"Ability [209]:")
    print(f"Cards: {ability.get('cards', [])}")
    print(f"Full text: {ability.get('full_text', '')}")
    print(f"Effect: {json.dumps(ability.get('effect'), indent=2, ensure_ascii=False)}")
else:
    print(f"Only {len(abilities)} abilities, index 209 not found")

# Search for the specific raw text in all abilities
for i, ability in enumerate(abilities):
    effect = ability.get('effect')
    if effect:
        def check_raw_text(obj):
            if isinstance(obj, dict):
                if 'raw_text' in obj:
                    if 'カード名が異なる' in obj['raw_text']:
                        print(f"\nFound at index {i}:")
                        print(f"Cards: {ability.get('cards', [])}")
                        print(f"Full text: {ability.get('full_text', '')}")
                        print(f"Raw text: {obj['raw_text']}")
                        print(f"Effect: {json.dumps(effect, indent=2, ensure_ascii=False)}")
                        return True
                for value in obj.values():
                    if check_raw_text(value):
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if check_raw_text(item):
                        return True
            return False
        
        if check_raw_text(effect):
            break
