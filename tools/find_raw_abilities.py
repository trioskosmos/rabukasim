#!/usr/bin/env python3
"""
Find the full abilities for the two remaining raw entries.
This script reads: data/abilities_extracted_from_cards.json
"""

import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find abilities with the two remaining raw costless_texts
raw_texts = [
    '(対戦相手のカードの効果でも発動する。)',
    '（手札のこのカードもこの効果で控え室に置ける。）'
]

for ab in data['unique_abilities']:
    full_text = ab.get('full_text', '')
    for raw_text in raw_texts:
        if raw_text in full_text:
            print("=" * 80)
            print(f"Costless: {ab.get('costless_text')}")
            print(f"Full Text: {ab.get('full_text')}")
            print(f"Triggerless Text: {ab.get('triggerless_text')}")
            print(f"Triggers: {ab.get('triggers')}")
            print(f"Card Count: {ab.get('card_count')}")
            print("=" * 80)
            print()
            break
