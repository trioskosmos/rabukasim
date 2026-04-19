import json

data = json.load(open('data/ability_frame_source.json', encoding='utf-8'))
abilities = data.get('abilities', [])

for a in abilities:
    if isinstance(a, dict) and 'text' in a:
        text = a.get('text', '')
        if 'Aqours' in text and ('ブレード' in text or 'blade' in text.lower()):
            print("Found Aqours + blade in generated frames:")
            print(json.dumps(a, indent=2, ensure_ascii=False)[:5000])
            break
