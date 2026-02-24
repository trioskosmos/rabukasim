#!/usr/bin/env python3
"""Extract unique abilities from cards.json for pseudocode writing."""
import json

cards = json.load(open('data/cards.json', encoding='utf-8'))

# Get unique abilities with their card numbers
ability_to_cards = {}
for card_no, card in cards.items():
    ability = card.get('ability', '')
    if ability:
        if ability not in ability_to_cards:
            ability_to_cards[ability] = []
        ability_to_cards[ability].append(card_no)

# Write unique abilities to file
with open('data/unique_abilities_extract.txt', 'w', encoding='utf-8') as f:
    for i, (ability, card_nos) in enumerate(ability_to_cards.items(), 1):
        f.write(f"=== ABILITY {i} ===\n")
        f.write(f"Cards: {', '.join(card_nos[:5])}")
        if len(card_nos) > 5:
            f.write(f" ... ({len(card_nos)} total)")
        f.write("\n")
        f.write(f"Japanese: {ability}\n\n")

print(f"Extracted {len(ability_to_cards)} unique abilities to data/unique_abilities_extract.txt")
