import json

data = json.load(open('data/ability_frame_source.json', encoding='utf-8'))
abilities = data.get('abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'text' in ability:
        text = ability.get('text', '')
        if 'Aqours' in text and 'ブレード' in text and '6' in text:
            print("Found Aqours + blade + 6 in generated frames:")
            print(json.dumps(ability, indent=2, ensure_ascii=False)[:8000])
            break
