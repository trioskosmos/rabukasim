#!/usr/bin/env python3
"""
Analyze costless abilities to determine best course of action.
This script reads: ../data/abilities_extracted_from_cards.json
This script writes: ../data/costless_analysis.txt
"""

import json

with open('../data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

costless_abilities = []
for ab in data['unique_abilities']:
    if ab.get('costless', False):
        costless_abilities.append(ab)

output = []
output.append("=" * 80)
output.append("COSTLESS ABILITIES ANALYSIS")
output.append("=" * 80)
output.append(f"Total abilities: {len(data['unique_abilities'])}")
output.append(f"Costless abilities: {len(costless_abilities)}")
output.append(f"Percentage: {len(costless_abilities) / len(data['unique_abilities']) * 100:.1f}%")
output.append("")

# Group by trigger
triggers = {}
for ab in costless_abilities:
    trigger = ab.get('triggers', 'None')
    if trigger not in triggers:
        triggers[trigger] = []
    triggers[trigger].append(ab)

output.append("\n" + "=" * 80)
output.append("BY TRIGGER")
output.append("=" * 80)
for trigger, items in sorted(triggers.items(), key=lambda x: -len(x[1])):
    output.append(f"\n{trigger}: {len(items)} abilities")
    for ab in items[:3]:  # Show first 3 examples
        output.append(f"  - {ab['triggerless_text'][:80]}")
    if len(items) > 3:
        output.append(f"  ... and {len(items) - 3} more")

# Show examples
output.append("\n" + "=" * 80)
output.append("EXAMPLES (first 20)")
output.append("=" * 80)
for i, ab in enumerate(costless_abilities[:20], 1):
    output.append(f"\n[{i}] Trigger: {ab.get('triggers', 'None')}")
    output.append(f"    Triggerless: {ab['triggerless_text'][:100]}")
    output.append(f"    Cards: {ab['card_count']}")

# Write to file
with open('../data/costless_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Analyzed {len(costless_abilities)} costless abilities")
print(f"Output written to ../data/costless_analysis.txt")
