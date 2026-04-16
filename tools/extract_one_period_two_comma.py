#!/usr/bin/env python3
"""
Extract one-period two-comma abilities to analyze raw text patterns.
"""
import json

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

one_period_two_comma = []

for ability in data['unique_abilities']:
    costless_text = ability['costless_text']
    
    # Count periods and commas
    period_count = costless_text.count('。')
    comma_count = costless_text.count('、')
    
    if period_count == 1 and comma_count == 2:
        one_period_two_comma.append(ability)

print(f"Total unique abilities: {len(data['unique_abilities'])}")
print(f"One-period two-comma: {len(one_period_two_comma)}")

# Write to file
with open('data/one_period_two_comma_abilities.txt', 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("ONE-PERIOD TWO-COMMA ABILITIES\n")
    f.write("="*80 + "\n")
    f.write(f"Total: {len(one_period_two_comma)}\n\n")
    
    for i, ability in enumerate(one_period_two_comma, 1):
        f.write(f"\n[{i}] Card count: {ability['card_count']}\n")
        f.write(f"    Triggers: {ability['triggers']}\n")
        f.write(f"    Costless text: {ability['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(ability['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text in effect
        effect = ability['effect']
        def check_for_raw(obj, path=""):
            if isinstance(obj, dict):
                if 'raw_text' in obj:
                    f.write(f"    RAW TEXT FOUND at {path}: {obj['raw_text']}\n")
                for key, value in obj.items():
                    check_for_raw(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for item in obj:
                    check_for_raw(item, path)
        
        check_for_raw(effect)

print(f"\nOutput written to data/one_period_two_comma_abilities.txt")
