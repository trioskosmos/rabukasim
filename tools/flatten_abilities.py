#!/usr/bin/env python3
"""
Flatten abilities_extracted_from_cards.json to remove nested arrays.
"""

import json

with open('../data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for ab in data['unique_abilities']:
    # Flatten card_examples to single example
    if 'card_examples' in ab and isinstance(ab['card_examples'], list):
        ab['card_example'] = ab['card_examples'][0] if ab['card_examples'] else None
        del ab['card_examples']
    
    # Flatten triggers to single string
    if 'triggers' in ab and isinstance(ab['triggers'], list):
        ab['triggers'] = ', '.join(ab['triggers']) if ab['triggers'] else None

with open('../data/abilities_extracted_from_cards.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Flattened abilities_extracted_from_cards.json")
