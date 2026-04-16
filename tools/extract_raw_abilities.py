#!/usr/bin/env python3
"""
Extract raw ability text (no variables, no semantics)
"""
import json

# Load abilities
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['unique_abilities']

# Extract just the raw text
raw_abilities = []
for ability in abilities:
    raw_abilities.append({
        "full_text": ability['full_text']
    })

# Save raw abilities
with open('data/raw_abilities.json', 'w', encoding='utf-8') as f:
    json.dump(raw_abilities, f, indent=2, ensure_ascii=False)

print(f"Extracted {len(raw_abilities)} raw abilities")
print("Saved to data/raw_abilities.json")
