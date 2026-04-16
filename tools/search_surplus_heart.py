#!/usr/bin/env python3
"""
Search for surplus heart condition abilities.
"""
import json

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for i, ability in enumerate(data['unique_abilities'], 1):
    costless_text = ability['costless_text']
    if '余剰ハート' in costless_text:
        print(f"[{i}] Costless text: {costless_text}")
        print(f"    Effect: {json.dumps(ability['effect'], indent=2, ensure_ascii=False)}")
        print()
