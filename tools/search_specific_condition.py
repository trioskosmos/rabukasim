#!/usr/bin/env python3
"""
Search for specific condition pattern to verify extraction.
"""
import json

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Search for the specific condition
for i, ability in enumerate(data['unique_abilities'], 1):
    costless_text = ability['costless_text']
    if '名前とコストが両方ともそれぞれ異なる' in costless_text:
        print(f"[{i}] Costless text: {costless_text}")
        print(f"    Effect: {json.dumps(ability['effect'], indent=2, ensure_ascii=False)}")
        print()
