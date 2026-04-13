#!/usr/bin/env python3
import json

with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find abilities with names in logic
examples = []
for ability in data['abilities']:
    logic = ability['source_ability_texts'][0]['logic']
    jp = ability['source_ability_texts'][0]['jp']
    cards = ability['source_ability_texts'][0]['cards']
    
    # Look for various name patterns in logic
    if any(pattern in logic for pattern in ['from ', 'name ', 'group ', 'with ']):
        if len(cards) > 0:
            examples.append({
                'card': cards[0],
                'jp': jp[:100],
                'logic': logic[:150]
            })
    
    if len(examples) >= 15:
        break

print('=== HOW NAMES GO TO LOGIC ===')
for ex in examples:
    print(f"\nCard: {ex['card']}")
    print(f"JP: {ex['jp']}...")
    print(f"LOGIC: {ex['logic']}...")
