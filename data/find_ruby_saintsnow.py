#!/usr/bin/env python3
"""Find which cards have the SaintSnow recovery ability."""
import json

with open('cards.json', 'r', encoding='utf-8') as f:
    cards_json = json.load(f)

# Look for cards with SaintSnow in the ability text  
search_text = "SaintSnow"

for card_no, card in cards_json.items():
    name = card.get('name', '')
    if '黒澤' in name or 'ルビィ' in name:
        ability = card.get('ability', '')
        if search_text in ability:
            print(f"{card_no}: {name}")
            print(f"  Ability (first 100 chars): {ability[:100]}")
            print()
