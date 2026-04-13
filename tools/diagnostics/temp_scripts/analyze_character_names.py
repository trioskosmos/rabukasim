#!/usr/bin/env python3
"""
Extract character names from cards.json and create mapping with no-space format.
"""

import json
import re

def load_cards():
    """Load cards_compiled.json."""
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_metadata():
    """Load metadata.json."""
    with open('data/metadata.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    cards = load_cards()
    metadata = load_metadata()
    
    # Get character IDs from metadata
    character_ids = metadata.get('character_ids', {})
    
    # Extract unique character names from cards_compiled.json
    # Structure: { "member_db": { card_id: {...} }, ... }
    character_names = set()
    cards_with_char_id = []
    
    member_db = cards.get('member_db', {})
    for card_id, card_data in member_db.items():
        name = card_data.get('name', '')
        char_id = card_data.get('char_id')
        if name:
            # Convert to no-space format
            no_space_name = name.replace(' ', '')
            character_names.add((name, no_space_name))
            if char_id:
                cards_with_char_id.append((name, no_space_name, char_id))
    
    print("Character Name Mapping (cards_compiled.json -> no-space format):")
    print("=" * 70)
    
    # Create mapping dictionary
    name_mapping = {}
    for original, no_space in sorted(character_names):
        name_mapping[no_space] = original
        print(f"{no_space} <- {original}")
    
    print(f"\nTotal unique character names: {len(character_names)}")
    
    # Now check which of these match the character IDs
    print("\n" + "=" * 70)
    print("Matching with metadata.json character_ids:")
    print("=" * 70)
    
    print(f"Cards with char_id field: {len(cards_with_char_id)}")
    
    # Create reverse mapping from char_id to name
    char_id_to_name = {}
    for name, no_space, char_id in cards_with_char_id:
        if char_id not in char_id_to_name:
            char_id_to_name[char_id] = no_space
    
    print(f"\nUnique char_id -> name mappings: {len(char_id_to_name)}")
    
    # Print the full mapping
    print("\n" + "=" * 70)
    print("CHARACTER_NAMES mapping for extract_abilities_to_template.py:")
    print("=" * 70)
    
    for char_id, no_space in sorted(char_id_to_name.items()):
        # Find the English name from character_ids
        english_name = None
        for en_name, en_id in character_ids.items():
            if en_id == char_id:
                english_name = en_name
                break
        if english_name:
            print(f'    "{no_space}": "{english_name}",')
    
    print(f"\n# Total mappings: {len(char_id_to_name)}")

if __name__ == '__main__':
    main()
