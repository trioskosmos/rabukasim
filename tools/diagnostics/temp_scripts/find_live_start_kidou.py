import json

data = json.load(open('data/abilities_extracted.json', encoding='utf-8'))

# Find the ability with both live_start and kidou triggers
for i, a in enumerate(data['abilities']):
    jp = a['source_ability_texts'][0].get('jp', '')
    if 'live_start' in jp and 'kidou' in jp:
        print(f"Index {i}:")
        print(f"  Trigger: {a.get('trigger', 'N/A')}")
        print(f"  Trigger ID: {a.get('trigger_id', 'N/A')}")
        print(f"  JP: {jp[:200]}...")
        print(f"  Logic: {a['source_ability_texts'][0]['logic'][:300]}...")
        print()
