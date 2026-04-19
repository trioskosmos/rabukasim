import json

data = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))
abilities = data.get('abilities', [])
print(f'Number of abilities: {len(abilities)}')
if len(abilities) > 0:
    print(f'First ability keys: {list(abilities[0].keys())}')
    print(f'First ability sample: {json.dumps(abilities[0], indent=2, ensure_ascii=False)[:2000]}')
