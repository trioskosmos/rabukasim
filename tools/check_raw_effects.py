#!/usr/bin/env python3
"""
Check for raw_text entries in effect field.
This script reads: data/abilities_extracted_from_cards.json
"""

import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check for raw_text in effect field
raw_count = 0
null_count = 0
non_null_count = 0
for ab in data['unique_abilities']:
    effect = ab.get('effect')
    if effect is None:
        null_count += 1
    elif isinstance(effect, dict) and 'raw_text' in effect:
        raw_count += 1
        print(f"Raw: {ab.get('costless_text', 'N/A')}")
        print(f"  Effect: {effect}")
    else:
        non_null_count += 1

print(f"\n" + "=" * 80)
print(f"Total abilities: {len(data['unique_abilities'])}")
print(f"Non-null effects: {non_null_count}")
print(f"Null effects: {null_count}")
print(f"Raw effects: {raw_count}")
print(f"Coverage: {non_null_count / len(data['unique_abilities']) * 100:.1f}%")
