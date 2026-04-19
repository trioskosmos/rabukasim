import json

data = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))
abilities = data.get('unique_abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'card_refs' in ability:
        for ref in ability['card_refs']:
            if '628' in str(ref):
                print("Found card 628 in semantic extraction:")
                print(json.dumps(ability, indent=2, ensure_ascii=False)[:5000])
                break
