import json

data = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))
for a in data:
    if isinstance(a, dict) and 'card_refs' in a:
        for ref in a['card_refs']:
            if '558' in str(ref.get('card_id', '')):
                print("Found card 558 in authored frames:")
                print(json.dumps(a.get('frames', []), indent=2, ensure_ascii=False)[:3000])
                break
