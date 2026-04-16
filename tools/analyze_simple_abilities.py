#!/usr/bin/env python3
"""
Analyze simple abilities - no comma, single full stop.
This script reads: ../data/abilities_extracted_from_cards.json
This script writes: ../data/simple_abilities_analysis.txt
"""

import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

simple_abilities = []
for ab in data['unique_abilities']:
    costless_text = ab.get('costless_text', '')
    # Simple: no comma, exactly one full stop
    if costless_text and '、' not in costless_text and costless_text.count('。') == 1:
        simple_abilities.append(ab)

output = []
output.append("=" * 80)
output.append("SIMPLE ABILITIES ANALYSIS")
output.append("=" * 80)
output.append(f"Total abilities: {len(data['unique_abilities'])}")
output.append(f"Simple abilities (no comma, single full stop): {len(simple_abilities)}")
output.append(f"Percentage: {len(simple_abilities) / len(data['unique_abilities']) * 100:.1f}%")
output.append("")

# Check uniqueness
unique_texts = list(set([ab['costless_text'] for ab in simple_abilities]))
output.append(f"Unique simple abilities: {len(unique_texts)}")
output.append(f"Duplicates: {len(simple_abilities) - len(unique_texts)}")
output.append("")

output.append("=" * 80)
output.append("ALL SIMPLE ABILITIES")
output.append("=" * 80)
for i, ab in enumerate(simple_abilities, 1):
    output.append(f"\n[{i}] Trigger: {ab.get('triggers', 'None')}")
    output.append(f"    Costless: {ab['costless_text']}")

# Write to file
with open('data/simple_abilities_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Analyzed {len(simple_abilities)} simple abilities")
print(f"Output written to ../data/simple_abilities_analysis.txt")
