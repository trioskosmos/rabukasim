import json

data = json.load(open('data/abilities_extracted.json', encoding='utf-8'))

print("Abilities with Japanese text in logic:\n")

count = 0
for i, a in enumerate(data['abilities']):
    logic = a['source_ability_texts'][0].get('logic', '')
    jp = a['source_ability_texts'][0].get('jp', '')
    
    if logic and any(ord(c) > 127 for c in logic):
        count += 1
        if count <= 10:  # Show first 10
            print(f"Index {i}:")
            print(f"  JP: {jp[:150]}...")
            print(f"  Logic: {logic[:200]}...")
            print()

print(f"Total: {count} abilities with Japanese text in logic")
