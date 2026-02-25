#!/usr/bin/env python
"""Update card_id_mapping.json with new cards from cards.json."""

import json
import os

def main():
    # Load existing mapping
    mapping_path = 'data/card_id_mapping.json'
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    # Load cards
    with open('data/cards.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)
    
    # Find max ID
    max_id = max(mapping.values()) if mapping else 0
    print(f"Current max ID: {max_id}")
    print(f"Current mapping count: {len(mapping)}")
    
    # Find new cards
    new_cards = []
    for card_id in cards.keys():
        if card_id not in mapping:
            new_cards.append(card_id)
    
    print(f"Found {len(new_cards)} new cards to add")
    
    # Add new cards with sequential IDs
    for card_id in sorted(new_cards):
        max_id += 1
        mapping[card_id] = max_id
    
    # Save updated mapping
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"Updated mapping saved. New max ID: {max_id}")
    print(f"Total mapping count: {len(mapping)}")

if __name__ == "__main__":
    main()
