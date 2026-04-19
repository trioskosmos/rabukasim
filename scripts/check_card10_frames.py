import json

data = json.load(open('data/cards_compiled.json', encoding='utf-8'))
card10 = data['member_db']['10']
print('Name:', card10['name'])
print('Abilities:', len(card10['abilities']))
for i, a in enumerate(card10['abilities']):
    if 'frame_program' in a:
        frames = a['frame_program']['frames']
        print(f'Ability {i}: {len(frames)} frames')
        for f in frames:
            print(f"  {f.get('frame_index')}: {f.get('op')} value={f.get('value')}")
