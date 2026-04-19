import json

data = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))
abilities = data.get('unique_abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'full_text' in ability:
        text = ability.get('full_text', '')
        if 'Aqours' in text and 'ブレード' in text and '6' in text:
            print("Found Aqours + blade + 6 in semantic extraction:")
            print(json.dumps(ability, indent=2, ensure_ascii=False)[:5000])
            break
