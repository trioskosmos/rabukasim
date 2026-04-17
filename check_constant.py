"""Check CONSTANT trigger abilities."""
import json

with open('data/ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

constant = [a for a in data['abilities'] if a.get('trigger') == 'CONSTANT']
print(f'CONSTANT abilities: {len(constant)}')

if constant:
    print('\n=== First 3 CONSTANT abilities ===')
    for i in range(min(3, len(constant))):
        ability = constant[i]
        print(f"\nAbility {i}: {ability['primary_text_jp'][:50]}...")
        print(f"Frames: {len(ability['frames'])}")
        for frame in ability['frames']:
            print(f"  {frame}")
