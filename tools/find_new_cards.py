#!/usr/bin/env python
"""Find new cards without pseudocode."""
import json

# Load cards
with open('data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

# Load old cards
with open('data/cards_old.json', 'r', encoding='utf-8') as f:
    old_cards = json.load(f)

# Load manual pseudocode
with open('data/manual_pseudocode.json', 'r', encoding='utf-8') as f:
    pseudocode = json.load(f)

# Find new cards
new_card_ids = set(cards.keys()) - set(old_cards.keys())

# Find cards without pseudocode
cards_without_pseudocode = [cid for cid in new_card_ids if cid not in pseudocode]

print(f'Total new cards: {len(new_card_ids)}')
print(f'New cards without pseudocode: {len(cards_without_pseudocode)}')
print()

# Show first 30
for i, cid in enumerate(sorted(cards_without_pseudocode)[:30]):
    card = cards[cid]
    ability = card.get('ability', '')
    card_type = card.get('type', 'Unknown')
    print(f'{i+1}. {cid}: {card.get("name", "Unknown")} ({card_type})')
    if ability:
        print(f'   Ability: {ability[:80]}...' if len(ability) > 80 else f'   Ability: {ability}')
    print()
