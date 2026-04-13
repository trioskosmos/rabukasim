#!/usr/bin/env python3
"""
Check for duplicate jp texts in extracted abilities.
"""

import json
from pathlib import Path
from collections import Counter

def check_duplicates(extracted_file):
    """Check for duplicate jp texts."""
    
    with open(extracted_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract all jp texts
    jp_texts = []
    for ability in data.get('abilities', []):
        source_texts = ability.get('source_ability_texts', [])
        if source_texts:
            jp_texts.append(source_texts[0].get('jp', ''))
    
    # Count duplicates
    text_counts = Counter(jp_texts)
    
    # Find duplicates
    duplicates = {text: count for text, count in text_counts.items() if count > 1}
    
    print(f"Total abilities: {len(jp_texts)}")
    print(f"Unique texts: {len(text_counts)}")
    print(f"Duplicate texts: {len(duplicates)}")
    
    if duplicates:
        print("\nDuplicate texts:")
        for text, count in duplicates.items():
            print(f"  Count: {count}")
            print(f"  Text: {text[:100]}...")
    else:
        print("\nNo duplicate texts found.")

if __name__ == "__main__":
    extracted_file = Path(__file__).parent.parent / "data" / "abilities_extracted.json"
    check_duplicates(extracted_file)
