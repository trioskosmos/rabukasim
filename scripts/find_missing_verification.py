import json

with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']
missing_verification = []
has_verification = []

for i, ability in enumerate(abilities):
    has_frame_verification = 'frame_verification' in ability
    if has_frame_verification:
        has_verification.append(i)
    else:
        missing_verification.append(i)

print(f'Total abilities: {len(abilities)}')
print(f'Has frame_verification: {len(has_verification)}')
print(f'Missing frame_verification: {len(missing_verification)}')

if missing_verification:
    print(f'\nMissing verification indices (first 20): {missing_verification[:20]}')
    
    # Print some examples
    print('\nFirst 3 abilities missing verification:')
    for idx in missing_verification[:3]:
        ability = abilities[idx]
        print(f'\nIndex {idx}:')
        print(f'  JP: {ability.get("primary_text_jp", "")[:100]}...')
        print(f'  Trigger: {ability.get("trigger", "N/A")}')
