#!/usr/bin/env python3
"""
Examine extracted abilities and compare outputs to verify quality.
"""
import json

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*80)
print("EXTRACTION QUALITY EXAMINATION")
print("="*80)
print(f"Total unique abilities: {len(data['unique_abilities'])}")
print()

# Sample some abilities with different trigger types
sample_indices = [0, 1, 2, 10, 20, 30, 50, 100, 150, 200]

for i in sample_indices:
    if i >= len(data['unique_abilities']):
        continue
    
    ability = data['unique_abilities'][i]
    
    print(f"\n{'='*80}")
    print(f"Ability #{i+1}")
    print(f"{'='*80}")
    print(f"Full text: {ability['full_text']}")
    print(f"Triggerless text: {ability['triggerless_text']}")
    print(f"Triggers: {ability['triggers']}")
    print(f"Costless: {ability['costless']}")
    print(f"Card count: {ability['card_count']}")
    print(f"\nCost:")
    print(json.dumps(ability['cost'], indent=2, ensure_ascii=False))
    print(f"\nEffect:")
    print(json.dumps(ability['effect'], indent=2, ensure_ascii=False))
    print(f"\nCostless text: {ability['costless_text']}")

# Also show some abilities with complex effects
print(f"\n\n{'='*80}")
print("COMPLEX ABILITIES (with compound or conditional effects)")
print(f"{'='*80}")

complex_count = 0
for i, ability in enumerate(data['unique_abilities']):
    effect = ability.get('effect')
    if effect:
        # Check for complex structures
        is_complex = False
        if isinstance(effect, dict):
            if 'actions' in effect:
                is_complex = True
            if 'condition' in effect:
                is_complex = True
        
        if is_complex:
            complex_count += 1
            if complex_count <= 5:  # Show first 5 complex abilities
                print(f"\n{'='*80}")
                print(f"Complex Ability #{i+1}")
                print(f"{'='*80}")
                print(f"Costless text: {ability['costless_text']}")
                print(f"\nEffect:")
                print(json.dumps(effect, indent=2, ensure_ascii=False))

print(f"\n\n{'='*80}")
print(f"Total complex abilities found: {complex_count}")
print(f"{'='*80}")
