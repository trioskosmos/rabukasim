#!/usr/bin/env python3
"""Find Wakana Shiki cards."""
import json

with open('cards.json', 'r', encoding='utf-8') as f:
    cards_json = json.load(f)

wakana_cards = []
for card_no, card in cards_json.items():
    name = card.get('name', '')
    if '若菜' in name:
        wakana_cards.append((card_no, name))

print(f"Found {len(wakana_cards)} Wakana cards:")
for card_no, name in wakana_cards[:10]:
    print(f"  {card_no}: {name}")
