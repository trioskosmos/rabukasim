#!/usr/bin/env python3
"""
Extract one-period zero-comma abilities for analysis.
"""
import json

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

one_p_zero_c = []

for i, ability in enumerate(data['unique_abilities'], 1):
    costless_text = ability['costless_text']
    if costless_text.count('。') == 1 and costless_text.count('、') == 0:
        one_p_zero_c.append({
            'index': i,
            'card_count': ability['card_count'],
            'triggers': ability['triggers'],
            'costless_text': costless_text,
            'effect': ability['effect']
        })

# Write to file
with open('data/one_period_zero_comma_abilities.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("ONE-PERIOD ZERO-COMMA ABILITIES\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(one_p_zero_c)}\n\n")
    
    for item in one_p_zero_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND at {effect_str}\n")
        
        f.write("\n")

print(f"Total one-period zero-comma: {len(one_p_zero_c)}")
print("Output written to data/one_period_zero_comma_abilities.txt")
