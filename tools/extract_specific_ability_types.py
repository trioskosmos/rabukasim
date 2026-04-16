#!/usr/bin/env python3
"""
Extract one-period only and one-period one-comma abilities.
"""
import json

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

one_period_only = []
one_period_one_comma = []

for ability in data['unique_abilities']:
    costless_text = ability['costless_text']
    
    # Count periods and commas
    period_count = costless_text.count('。')
    comma_count = costless_text.count('、')
    
    if period_count == 1 and comma_count == 0:
        one_period_only.append(ability)
    elif period_count == 1 and comma_count == 1:
        one_period_one_comma.append(ability)

print(f"Total unique abilities: {len(data['unique_abilities'])}")
print(f"One-period only: {len(one_period_only)}")
print(f"One-period one-comma: {len(one_period_one_comma)}")

# Write to files
with open('data/one_period_only_abilities.txt', 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("ONE-PERIOD ONLY ABILITIES\n")
    f.write("="*80 + "\n")
    f.write(f"Total: {len(one_period_only)}\n\n")
    
    for i, ability in enumerate(one_period_only, 1):
        f.write(f"\n[{i}] Card count: {ability['card_count']}\n")
        f.write(f"    Triggers: {ability['triggers']}\n")
        f.write(f"    Costless text: {ability['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(ability['effect'], indent=2, ensure_ascii=False)}\n")

with open('data/one_period_one_comma_abilities.txt', 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("ONE-PERIOD ONE-COMMA ABILITIES\n")
    f.write("="*80 + "\n")
    f.write(f"Total: {len(one_period_one_comma)}\n\n")
    
    for i, ability in enumerate(one_period_one_comma, 1):
        f.write(f"\n[{i}] Card count: {ability['card_count']}\n")
        f.write(f"    Triggers: {ability['triggers']}\n")
        f.write(f"    Costless text: {ability['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(ability['effect'], indent=2, ensure_ascii=False)}\n")

print(f"\nOutput written to:")
print(f"  - data/one_period_only_abilities.txt")
print(f"  - data/one_period_one_comma_abilities.txt")
