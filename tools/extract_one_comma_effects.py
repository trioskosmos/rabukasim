#!/usr/bin/env python3
"""
Extract and output one comma one period costless abilities with their extracted effects.
This script reads: data/abilities_extracted_from_cards.json
This script writes: data/one_comma_one_period_effects.txt
"""

import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filter to costless abilities with 1 comma and 1 full stop
one_comma_abilities = []
for ab in data['unique_abilities']:
    costless_text = ab.get('costless_text', '')
    if ab.get('costless') and costless_text and costless_text.count('、') == 1 and costless_text.count('。') == 1:
        one_comma_abilities.append(ab)

output = []
output.append("=" * 80)
output.append("ONE COMMA ONE PERIOD COSTLESS ABILITIES WITH EXTRACTED EFFECTS")
output.append("=" * 80)
output.append(f"Total: {len(one_comma_abilities)}")
output.append("")

for i, ab in enumerate(one_comma_abilities, 1):
    output.append(f"\n[{i}] Trigger: {ab.get('triggers', 'None')}")
    output.append(f"    Costless: {ab['costless_text']}")
    output.append(f"    Effect: {json.dumps(ab.get('effect'), indent=4, ensure_ascii=False)}")

# Write to file
with open('data/one_comma_one_period_effects.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Extracted {len(one_comma_abilities)} one comma one period costless abilities")
print(f"Output written to data/one_comma_one_period_effects.txt")
