import json

data = json.load(open('data/abilities_extracted.json', encoding='utf-8'))

print(f"Total abilities: {len(data['abilities'])}\n")

# Count empty, Japanese, and incomplete logic
empty_count = 0
japanese_count = 0
incomplete_count = 0

for i, a in enumerate(data['abilities']):
    logic = a['source_ability_texts'][0].get('logic', '')
    jp = a['source_ability_texts'][0].get('jp', '')
    
    if not logic:
        empty_count += 1
    elif any(ord(c) > 127 for c in logic):  # Contains non-ASCII (Japanese)
        japanese_count += 1
        if i < 5:  # Show first 5 examples
            print(f"Index {i} (Japanese in logic):")
            print(f"  JP: {jp[:100]}...")
            print(f"  Logic: {logic[:150]}...")
            print()
    elif 'if' in logic and not logic.endswith(('draw', 'discard', 'add', 'tap', 'recover', 'play', 'untap', 'activate', 'set', 'reduce', 'move', 'select', 'change', 'place', 'remove', 'swap', 'look', 'reorder', 'negate', 'grant', 'apply', 'trigger', 'repeat', 'skip', 'prevent')):
        # Might be incomplete if condition but no clear action
        incomplete_count += 1
        if i < 3:
            print(f"Index {i} (Potentially incomplete):")
            print(f"  JP: {jp[:100]}...")
            print(f"  Logic: {logic[:150]}...")
            print()

print(f"\nStatistics:")
print(f"  Empty logic: {empty_count} ({empty_count/len(data['abilities'])*100:.1f}%)")
print(f"  Japanese text in logic: {japanese_count} ({japanese_count/len(data['abilities'])*100:.1f}%)")
print(f"  Potentially incomplete: {incomplete_count} ({incomplete_count/len(data['abilities'])*100:.1f}%)")
