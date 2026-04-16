#!/usr/bin/env python3
"""
Check if effect field was added to abilities_extracted_from_cards.json
"""

import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check for effect field
effect_count = 0
non_null_effect_count = 0
for ab in data['unique_abilities']:
    if 'effect' in ab:
        effect_count += 1
        if ab['effect']:
            non_null_effect_count += 1

print(f"Abilities with effect field: {effect_count}/{len(data['unique_abilities'])}")
print(f"Abilities with non-null effect: {non_null_effect_count}/{len(data['unique_abilities'])}")
