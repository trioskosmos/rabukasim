#!/usr/bin/env python3
import json

with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

# Find these specific cards
card_ids = ['PL!HS-PR-010-PR', 'PL!HS-PR-011-PR', 'PL!HS-bp1-019-L']
for card_id in card_ids:
    if card_id in cards:
        card = cards[card_id]
        print(f'=== {card_id} ===')
        print(f"Name: {card.get('name', 'N/A')}")
        ability = card.get('ability', 'N/A')
        print(f"Ability: {ability[:200]}...")
        print()
