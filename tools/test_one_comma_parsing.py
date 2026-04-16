#!/usr/bin/env python3
"""
Test if parse_backwards can be applied to each clause in one-comma abilities.
This script reads: data/abilities_extracted_from_cards.json
"""

import json
import re
import sys
sys.path.append('tools/ability_extraction')

# Import the parsing functions from extract_costs.py
from extract_costs import parse_effect_backwards

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filter to costless abilities with 1 comma and 1 full stop
one_comma_abilities = []
for ab in data['unique_abilities']:
    costless_text = ab.get('costless_text', '')
    if ab.get('costless') and costless_text and costless_text.count('、') == 1 and costless_text.count('。') == 1:
        one_comma_abilities.append(ab)

print(f"Testing {len(one_comma_abilities)} one-comma abilities")
print("=" * 80)

success_count = 0
for i, ab in enumerate(one_comma_abilities[:20], 1):  # Test first 20
    costless_text = ab.get('costless_text', '')
    
    # Split on comma
    parts = costless_text.split('、')
    
    print(f"\n[{i}] {costless_text}")
    print(f"  Part 1: {parts[0]}")
    result1 = parse_effect_backwards(parts[0].rstrip('。'))
    print(f"    Parsed: {result1}")
    
    if len(parts) > 1:
        print(f"  Part 2: {parts[1]}")
        result2 = parse_effect_backwards(parts[1].rstrip('。'))
        print(f"    Parsed: {result2}")
    
    # Check if both parts parsed successfully
    if result1 and result1.get('action') and (len(parts) == 1 or (result2 and result2.get('action'))):
        success_count += 1
        print(f"  ✓ Both parts parsed successfully")
    else:
        print(f"  ✗ Parsing failed")

print(f"\n" + "=" * 80)
print(f"Success rate: {success_count}/20 = {success_count/20*100:.1f}%")
