#!/usr/bin/env python
"""Generate pseudocodes for new cards based on unique abilities."""
import json
import re

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

# Group cards by similar abilities
ability_groups = {}
for cid in cards_without_pseudocode:
    card = cards[cid]
    ability = card.get('ability', '')
    card_type = card.get('type', '')
    
    # Skip energy cards without abilities
    if card_type == 'エネルギー' and not ability:
        continue
    
    if ability:
        # Normalize ability text for grouping
        normalized = ability.strip()
        if normalized not in ability_groups:
            ability_groups[normalized] = []
        ability_groups[normalized].append(cid)

print(f'\nUnique ability patterns: {len(ability_groups)}')

# Show unique abilities with their cards
print('\n=== UNIQUE ABILITIES ===\n')
for i, (ability, card_ids) in enumerate(sorted(ability_groups.items()), 1):
    print(f'--- Pattern {i} ({len(card_ids)} cards) ---')
    print(f'Cards: {", ".join(card_ids[:5])}{"..." if len(card_ids) > 5 else ""}')
    print(f'Ability: {ability[:150]}{"..." if len(ability) > 150 else ""}')
    print()
