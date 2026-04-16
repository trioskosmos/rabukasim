#!/usr/bin/env python3
"""
Search for remaining raw conditions in extracted abilities.
"""
import json

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

raw_conditions = []
condition_prefixes = []

for i, ability in enumerate(data['unique_abilities'], 1):
    effect = ability.get('effect')
    if not effect:
        continue
    
    def check_for_raw(obj, path=""):
        if isinstance(obj, dict):
            if 'type' in obj and obj['type'] == 'raw':
                raw_conditions.append({
                    'index': i,
                    'path': path,
                    'text': obj.get('text', ''),
                    'costless_text': ability['costless_text']
                })
            if 'condition_prefix' in obj:
                condition_prefixes.append({
                    'index': i,
                    'path': path,
                    'prefix': obj['condition_prefix'],
                    'costless_text': ability['costless_text']
                })
            for key, value in obj.items():
                check_for_raw(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for item in obj:
                check_for_raw(item, path)
    
    check_for_raw(effect)

print(f"Total abilities with 'type: raw': {len(raw_conditions)}")
print(f"Total abilities with 'condition_prefix': {len(condition_prefixes)}")

if raw_conditions:
    print("\n" + "="*80)
    print("RAW CONDITIONS")
    print("="*80)
    for item in raw_conditions[:20]:  # Show first 20
        print(f"\n[{item['index']}] {item['path']}")
        print(f"    Raw text: {item['text']}")
        print(f"    Costless text: {item['costless_text']}")

if condition_prefixes:
    print("\n" + "="*80)
    print("CONDITION PREFIXES")
    print("="*80)
    for item in condition_prefixes[:20]:  # Show first 20
        print(f"\n[{item['index']}] {item['path']}")
        print(f"    Prefix: {item['prefix']}")
        print(f"    Costless text: {item['costless_text']}")
