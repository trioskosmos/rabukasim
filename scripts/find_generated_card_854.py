import json

data = json.load(open('data/ability_frame_source.json', encoding='utf-8'))
abilities = data.get('abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'card_refs' in ability:
        for ref in ability['card_refs']:
            if 'PL!SP-bp5-001-AR' in str(ref.get('card_no', '')):
                print(f"Found PL!SP-bp5-001-AR in generated frames:")
                print(json.dumps(ability, indent=2, ensure_ascii=False)[:8000])
                break
