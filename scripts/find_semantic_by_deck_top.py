import json

data = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))
abilities = data.get('unique_abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'full_text' in ability:
        text = ability.get('full_text', '')
        if 'デッキの一番上のカードを控え室に置いてもよい' in text:
            print("Found semantic extraction with deck top discard:")
            print(json.dumps(ability, indent=2, ensure_ascii=False)[:5000])
            break
