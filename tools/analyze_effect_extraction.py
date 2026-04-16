#!/usr/bin/env python3
"""
Analyze effect extraction results.
This script reads: ../data/abilities_extracted_from_cards.json
This script writes: ../data/effect_extraction_analysis.txt
"""

import json

with open('../data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Analyze effect extraction
with_effect = 0
without_effect = 0
effect_types = {}

for ab in data['unique_abilities']:
    effect = ab.get('effect')
    if effect:
        with_effect += 1
        for key in effect.keys():
            if key not in effect_types:
                effect_types[key] = 0
            effect_types[key] += 1
    else:
        without_effect += 1

output = []
output.append("=" * 80)
output.append("EFFECT EXTRACTION ANALYSIS")
output.append("=" * 80)
output.append(f"Total abilities: {len(data['unique_abilities'])}")
output.append(f"With effect: {with_effect} ({with_effect/len(data['unique_abilities'])*100:.1f}%)")
output.append(f"Without effect: {without_effect} ({without_effect/len(data['unique_abilities'])*100:.1f}%)")
output.append("")

output.append("=" * 80)
output.append("EFFECT TYPES")
output.append("=" * 80)
for effect_type, count in sorted(effect_types.items(), key=lambda x: -x[1]):
    output.append(f"{effect_type}: {count}")

output.append("\n" + "=" * 80)
output.append("EXAMPLES OF EXTRACTED EFFECTS")
output.append("=" * 80)

# Show examples for each effect type
for ab in data['unique_abilities'][:20]:
    effect = ab.get('effect')
    if effect:
        output.append(f"\nCostless: {ab.get('costless_text', '')[:80]}")
        output.append(f"Effect: {effect}")

# Write to file
with open('../data/effect_extraction_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Analyzed {len(data['unique_abilities'])} abilities")
print(f"Effects extracted: {with_effect}")
print(f"Output written to ../data/effect_extraction_analysis.txt")
