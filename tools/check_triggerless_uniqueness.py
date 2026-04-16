#!/usr/bin/env python3
"""
Check how many unique triggerless_text values exist compared to full_text.
"""

import json
from pathlib import Path


def check_triggerless_uniqueness():
    """Check uniqueness of triggerless_text vs full_text."""
    
    # Load abilities
    abilities_file = Path("data/abilities_extracted_from_cards.json")
    with open(abilities_file, encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data["unique_abilities"]
    
    # Count unique values
    full_texts = set(ability["full_text"] for ability in abilities)
    triggerless_texts = set(ability["triggerless_text"] for ability in abilities)
    
    print(f"=== Uniqueness Check ===")
    print(f"Total abilities: {len(abilities)}")
    print(f"Unique full_text: {len(full_texts)}")
    print(f"Unique triggerless_text: {len(triggerless_texts)}")
    print(f"Difference: {len(full_texts) - len(triggerless_texts)}")
    print()
    
    # Find triggerless_texts that map to multiple full_texts
    triggerless_to_full = {}
    for ability in abilities:
        triggerless = ability["triggerless_text"]
        full = ability["full_text"]
        if triggerless not in triggerless_to_full:
            triggerless_to_full[triggerless] = []
        triggerless_to_full[triggerless].append(full)
    
    # Find duplicates
    duplicates = {k: v for k, v in triggerless_to_full.items() if len(v) > 1}
    
    print(f"Triggerless texts with multiple full_texts: {len(duplicates)}")
    print()
    
    # Show some examples
    print("=== Examples of triggerless_text mapping to multiple full_texts ===")
    for i, (triggerless, fulls) in enumerate(list(duplicates.items())[:5]):
        print(f"\nExample {i+1}:")
        print(f"Triggerless: {triggerless}")
        print(f"Maps to {len(fulls)} full_texts:")
        for full in fulls:
            print(f"  - {full}")


if __name__ == "__main__":
    check_triggerless_uniqueness()
