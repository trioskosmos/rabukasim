import json

data = json.load(open('data/cards_compiled.json', encoding='utf-8'))
card709 = data['live_db']['709']
print('Name:', card709['name'])
print('Abilities:', len(card709['abilities']))
for i, a in enumerate(card709['abilities']):
    print(f'Ability {i}: trigger={a.get("trigger")}')
    if 'frame_program' in a:
        frames = a['frame_program']['frames']
        print(f'  Frames: {len(frames)}')
        for f in frames:
            print(f"    {f.get('frame_index')}: {f.get('op')} value={f.get('value')}")
