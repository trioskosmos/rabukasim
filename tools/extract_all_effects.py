#!/usr/bin/env python3
"""
Extract all effects and output for examination.
This script reads: data/abilities_extracted_from_cards.json
This script writes: data/all_effects.txt and data/all_effects.json
"""

import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

output = []
json_output = []

output.append("=" * 80)
output.append("ALL COSTLESS TEXTS WITH EXTRACTED EFFECTS")
output.append("=" * 80)

for i, ab in enumerate(data['unique_abilities'], 1):
    costless_text = ab.get('costless_text', '')
    effect = ab.get('effect')
    
    output.append(f"\n[{i}] Costless: {costless_text}")
    output.append(f"    Effect: {effect}")
    
    json_output.append({
        'index': i,
        'costless_text': costless_text,
        'effect': effect
    })

with open('data/all_effects.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

with open('data/all_effects.json', 'w', encoding='utf-8') as f:
    json.dump(json_output, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(data['unique_abilities'])} effects")
print(f"Output written to data/all_effects.txt and data/all_effects.json")
