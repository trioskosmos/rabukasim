import json

data = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))
abilities = data.get('abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'card_refs' in ability:
        for ref in ability['card_refs']:
            if '459' in str(ref):
                print("Found card 459 in authored frames:")
                print(json.dumps(ability, indent=2, ensure_ascii=False)[:5000])
                break
