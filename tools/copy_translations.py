#!/usr/bin/env python3
"""
Copy manual_pseudocode and manual_translations_en entries to new cards with the same ability text.

This tool finds cards in cards.json that have the same ability text as cards in cards_old.json,
and copies the pseudocode and English translation entries to the new cards.

Usage:
    python tools/copy_translations.py
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Main entry point."""
    old_cards_path = "data/cards_old.json"
    new_cards_path = "data/cards.json"
    pseudocode_path = "data/manual_pseudocode.json"
    translations_path = "data/manual_translations_en.json"
    
    # Load cards
    print(f"Loading {old_cards_path}...")
    with open(old_cards_path, 'r', encoding='utf-8') as f:
        old_cards = json.load(f)
    
    print(f"Loading {new_cards_path}...")
    with open(new_cards_path, 'r', encoding='utf-8') as f:
        new_cards = json.load(f)
    
    # Load existing pseudocode and translations
    print(f"Loading {pseudocode_path}...")
    with open(pseudocode_path, 'r', encoding='utf-8') as f:
        pseudocode = json.load(f)
    
    print(f"Loading {translations_path}...")
    with open(translations_path, 'r', encoding='utf-8') as f:
        translations = json.load(f)
    
    # Build ability -> card_no mapping from old cards
    print("\nBuilding ability text index from old cards...")
    ability_to_old_cards = {}  # ability_text -> [card_nos]
    
    for card_no, card_data in old_cards.items():
        ability = card_data.get("ability", "")
        if ability:
            if ability not in ability_to_old_cards:
                ability_to_old_cards[ability] = []
            ability_to_old_cards[ability].append(card_no)
    
    print(f"Found {len(ability_to_old_cards)} unique ability texts in old cards")
    
    # Find new cards with same ability text
    print("\nFinding new cards with matching ability text...")
    new_pseudocode_entries = {}
    new_translation_entries = {}
    
    for card_no, card_data in new_cards.items():
        ability = card_data.get("ability", "")
        if not ability:
            continue
        
        # Skip if already has pseudocode
        if card_no in pseudocode:
            continue
        
        # Check if this ability exists in old cards
        if ability in ability_to_old_cards:
            old_card_nos = ability_to_old_cards[ability]
            
            # Find an old card that has pseudocode
            for old_card_no in old_card_nos:
                if old_card_no in pseudocode:
                    # Copy pseudocode
                    new_pseudocode_entries[card_no] = pseudocode[old_card_no]
                    print(f"  [PSEUDO] {card_no} <- {old_card_no}")
                    break
            
            # Find an old card that has translation
            for old_card_no in old_card_nos:
                if old_card_no in translations:
                    # Copy translation
                    new_translation_entries[card_no] = translations[old_card_no]
                    print(f"  [TRANS] {card_no} <- {old_card_no}")
                    break
    
    print(f"\nNew pseudocode entries: {len(new_pseudocode_entries)}")
    print(f"New translation entries: {len(new_translation_entries)}")
    
    if not new_pseudocode_entries and not new_translation_entries:
        print("\nNo new entries to add.")
        return
    
    # Merge and save
    print("\nMerging entries...")
    
    # Update pseudocode
    updated_pseudocode = dict(pseudocode)
    updated_pseudocode.update(new_pseudocode_entries)
    
    # Update translations
    updated_translations = dict(translations)
    updated_translations.update(new_translation_entries)
    
    # Save
    print(f"Saving {pseudocode_path}...")
    with open(pseudocode_path, 'w', encoding='utf-8') as f:
        json.dump(updated_pseudocode, f, ensure_ascii=False, indent=4)
    
    print(f"Saving {translations_path}...")
    with open(translations_path, 'w', encoding='utf-8') as f:
        json.dump(updated_translations, f, ensure_ascii=False, indent=4)
    
    print("\nDone!")
    print(f"Total pseudocode entries: {len(updated_pseudocode)}")
    print(f"Total translation entries: {len(updated_translations)}")


if __name__ == "__main__":
    main()
