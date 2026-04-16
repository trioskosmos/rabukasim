#!/usr/bin/env python3
"""
Analyze costless abilities with 1 comma and 1 full stop.
This script reads: data/abilities_extracted_from_cards.json
This script writes: data/one_comma_abilities_analysis.txt
"""

import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filter to costless abilities with 1 comma and 1 full stop
one_comma_abilities = []
for ab in data['unique_abilities']:
    costless_text = ab.get('costless_text', '')
    # Costless: no cost, 1 comma, exactly 1 full stop
    if ab.get('costless') and costless_text and costless_text.count('、') == 1 and costless_text.count('。') == 1:
        one_comma_abilities.append(ab)

output = []
output.append("=" * 80)
output.append("ONE COMMA COSTLESS ABILITIES ANALYSIS")
output.append("=" * 80)
output.append(f"Total unique abilities: {len(data['unique_abilities'])}")
output.append(f"One comma costless abilities: {len(one_comma_abilities)}")
output.append(f"Percentage: {len(one_comma_abilities) / len(data['unique_abilities']) * 100:.1f}%")
output.append("")

output.append("=" * 80)
output.append("TRIGGER DISTRIBUTION")
output.append("=" * 80)
trigger_counts = {}
for ab in one_comma_abilities:
    trigger = ab.get('triggers', 'None')
    trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
for trigger, count in sorted(trigger_counts.items(), key=lambda x: -x[1]):
    output.append(f"{trigger}: {count}")

output.append("")
output.append("=" * 80)
output.append("ALL ONE COMMA COSTLESS ABILITIES")
output.append("=" * 80)
for i, ab in enumerate(one_comma_abilities, 1):
    output.append(f"\n[{i}] Trigger: {ab.get('triggers', 'None')}")
    output.append(f"    Costless: {ab['costless_text']}")

# Write to file
with open('data/one_comma_abilities_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Analyzed {len(one_comma_abilities)} one comma costless abilities")
print(f"Output written to data/one_comma_abilities_analysis.txt")
