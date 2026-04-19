import json

data = json.load(open('data/ability_frame_source.json', encoding='utf-8'))
abilities = data.get('abilities', [])

for a in abilities:
    if isinstance(a, dict) and 'card_refs' in a:
        for ref in a['card_refs']:
            if '459' in str(ref.get('card_id', '')):
                print("Found card 459 in generated frames:")
                print(json.dumps(a, indent=2, ensure_ascii=False)[:5000])
                break
