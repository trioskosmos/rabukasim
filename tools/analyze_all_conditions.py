#!/usr/bin/env python3
"""
Extract and analyze all conditions to identify missing details.
"""
import json
from collections import defaultdict

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

conditions_by_type = defaultdict(list)
total_conditions = 0

def extract_conditions(obj, ability_index, costless_text):
    global total_conditions
    if isinstance(obj, dict):
        if 'condition' in obj:
            cond = obj['condition']
            cond_type = cond.get('type', 'unknown')
            conditions_by_type[cond_type].append({
                'index': ability_index,
                'condition': cond,
                'action': obj.get('action'),
                'costless_text': costless_text
            })
            total_conditions += 1
        for key, value in obj.items():
            extract_conditions(value, ability_index, costless_text)
    elif isinstance(obj, list):
        for item in obj:
            extract_conditions(item, ability_index, costless_text)

for i, ability in enumerate(data['unique_abilities'], 1):
    effect = ability.get('effect')
    if not effect:
        continue
    extract_conditions(effect, i, ability['costless_text'])

print(f"Total conditions found: {total_conditions}")
print(f"Unique condition types: {len(conditions_by_type)}")
print()

# Analyze each condition type
for cond_type, conditions in sorted(conditions_by_type.items()):
    print(f"\n{'='*80}")
    print(f"Condition Type: {cond_type} ({len(conditions)} abilities)")
    print(f"{'='*80}")
    
    # Show sample conditions
    for i, item in enumerate(conditions[:5], 1):
        print(f"\n  [{i}] Ability #{item['index']}")
        print(f"      Costless text: {item['costless_text']}")
        print(f"      Condition: {json.dumps(item['condition'], indent=6, ensure_ascii=False)}")
        if item['action']:
            print(f"      Action: {json.dumps(item['action'], indent=6, ensure_ascii=False)}")
    
    if len(conditions) > 5:
        print(f"\n  ... and {len(conditions) - 5} more")
    
    # Analyze parameter coverage
    all_keys = set()
    for item in conditions:
        all_keys.update(item['condition'].keys())
    
    print(f"\n  Parameters found: {', '.join(sorted(all_keys))}")

# Write detailed analysis to file
with open('data/condition_analysis.txt', 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("CONDITION ANALYSIS\n")
    f.write("="*80 + "\n")
    f.write(f"Total conditions found: {total_conditions}\n")
    f.write(f"Unique condition types: {len(conditions_by_type)}\n\n")
    
    for cond_type, conditions in sorted(conditions_by_type.items()):
        f.write(f"\n{'='*80}\n")
        f.write(f"Condition Type: {cond_type} ({len(conditions)} abilities)\n")
        f.write(f"{'='*80}\n")
        
        for item in conditions:
            f.write(f"\nAbility #{item['index']}\n")
            f.write(f"  Costless text: {item['costless_text']}\n")
            f.write(f"  Condition: {json.dumps(item['condition'], indent=2, ensure_ascii=False)}\n")
            if item['action']:
                f.write(f"  Action: {json.dumps(item['action'], indent=2, ensure_ascii=False)}\n")

print(f"\nDetailed analysis written to data/condition_analysis.txt")
