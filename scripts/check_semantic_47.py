#!/usr/bin/env python3
"""Check semantic extraction for card 47"""
import json

with open('data/abilities_extracted_from_cards.json', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('unique_abilities', [])
for ability in abilities:
    cards = ability.get('cards', [])
    for card in cards:
        if 'PL!-bp3-024-L' in card:
            print("Found in semantic extraction:")
            print(json.dumps(ability, ensure_ascii=False, indent=2))
