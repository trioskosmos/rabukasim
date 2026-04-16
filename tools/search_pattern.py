#!/usr/bin/env python3
"""
Search for a specific pattern in abilities_extracted_from_cards.json and show full ability details.
"""
import json
import sys

# Pattern to search for
SEARCH_PATTERN = "{{center.png|センター}}自分のステージにいるすべての『Liella!』のメンバーと"

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Search through unique abilities
found_count = 0
for i, ability in enumerate(data['unique_abilities'], 1):
    full_text = ability.get('full_text', '')
    costless_text = ability.get('costless_text', '')
    
    if SEARCH_PATTERN in full_text or SEARCH_PATTERN in costless_text:
        found_count += 1
        print(f"\n{'='*80}")
        print(f"Match #{found_count}")
        print(f"{'='*80}")
        print(f"Full text: {full_text}")
        print(f"Triggerless text: {ability.get('triggerless_text', 'N/A')}")
        print(f"Triggers: {ability.get('triggers', 'N/A')}")
        print(f"Card count: {ability.get('card_count', 'N/A')}")
        print(f"Costless text: {costless_text}")
        print(f"\nCurrent effect output:")
        print(json.dumps(ability.get('effect'), indent=2, ensure_ascii=False))
        print(f"\nCards:")
        for card in ability.get('cards', []):
            print(f"  - {card}")

print(f"\n{'='*80}")
print(f"Total matches found: {found_count}")
print(f"{'='*80}")
