"""Check generated frame structure."""
import json

with open('data/ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total abilities: {len(data["abilities"])}')
print('\n=== First 3 abilities frame structures ===')
for i in range(min(3, len(data['abilities']))):
    ability = data['abilities'][i]
    print(f"\nAbility {i}: {ability['primary_text_jp'][:50]}...")
    print(f"Trigger: {ability['trigger']}")
    print(f"Frames: {len(ability['frames'])}")
    for frame in ability['frames'][:5]:
        print(f"  {frame}")
