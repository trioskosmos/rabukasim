"""Find card 10 in cards.json to understand its ability text."""

import json

with open('data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

# Find card 10
for card_id, card in cards.items():
    if '10' in card_id and 'PL!' in card_id:
        ability = card.get('ability', '')
        if ability:
            print(f"Card ID: {card_id}")
            print(f"Name: {card.get('name', '')}")
            print(f"Ability: {ability}")
            print()
