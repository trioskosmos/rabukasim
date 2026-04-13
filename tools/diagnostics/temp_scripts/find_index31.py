import json

data = json.load(open('data/abilities_extracted.json', encoding='utf-8'))

# Find Index 31 (the 32nd entry, 0-indexed)
if len(data['abilities']) > 31:
    entry = data['abilities'][31]
    print(f"Index 31 entry:")
    print(f"  Trigger: {entry.get('trigger', 'N/A')}")
    print(f"  Trigger ID: {entry.get('trigger_id', 'N/A')}")
    print(f"  JP: {entry['source_ability_texts'][0]['jp'][:200]}...")
    print(f"  Logic: {entry['source_ability_texts'][0]['logic'][:300]}...")
    print()
    
    # Check if there are other entries with the same cards (might be split triggers)
    cards = entry['source_ability_texts'][0]['cards']
    print(f"Cards for this entry: {cards[:2]}")
    print()
    
    # Find all entries with these cards
    for i, a in enumerate(data['abilities']):
        if a['source_ability_texts'][0]['cards'] == cards:
            print(f"Entry {i} has same cards:")
            print(f"  Trigger: {a.get('trigger', 'N/A')}")
            print(f"  JP: {a['source_ability_texts'][0]['jp'][:200]}...")
            print()
