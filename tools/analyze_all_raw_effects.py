#!/usr/bin/env python3
"""
Analyze all raw_text entries in effect extraction to identify missing patterns.
This script reads: data/abilities_extracted_from_cards.json
This script writes: data/all_raw_effects_analysis.txt
"""

import json

def extract_raw_text(effect):
    """Extract all raw_text values from effect dictionary recursively."""
    raw_texts = []
    
    if effect is None:
        return raw_texts
    
    if isinstance(effect, dict):
        if 'raw_text' in effect:
            raw_texts.append(effect['raw_text'])
        if 'condition' in effect and isinstance(effect['condition'], dict):
            if 'raw_text' in effect['condition']:
                raw_texts.append(effect['condition']['raw_text'])
        if 'actions' in effect and isinstance(effect['actions'], list):
            for action in effect['actions']:
                raw_texts.extend(extract_raw_text(action))
    
    return raw_texts

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find all raw_text entries
all_raw_texts = []
for ab in data['unique_abilities']:
    effect = ab.get('effect')
    raw_texts = extract_raw_text(effect)
    if raw_texts:
        all_raw_texts.append({
            'costless_text': ab.get('costless_text', ''),
            'raw_texts': raw_texts,
            'triggers': ab.get('triggers', 'None')
        })

output = []
output.append("=" * 80)
output.append("ALL RAW_TEXT ENTRIES IN EFFECT EXTRACTION")
output.append("=" * 80)
output.append(f"Total abilities with raw_text: {len(all_raw_texts)}")
output.append(f"Total unique abilities: {len(data['unique_abilities'])}")
output.append("")

output.append("=" * 80)
output.append("RAW_TEXT ENTRIES BY ABILITY")
output.append("=" * 80)

for i, entry in enumerate(all_raw_texts, 1):
    output.append(f"\n[{i}] Costless: {entry['costless_text']}")
    output.append(f"    Triggers: {entry['triggers']}")
    for j, raw_text in enumerate(entry['raw_texts'], 1):
        output.append(f"    Raw {j}: {raw_text}")

# Count unique raw_text patterns
unique_raw_texts = set()
for entry in all_raw_texts:
    for raw_text in entry['raw_texts']:
        unique_raw_texts.add(raw_text)

output.append("")
output.append("=" * 80)
output.append("UNIQUE RAW_TEXT PATTERNS")
output.append("=" * 80)
output.append(f"Total unique patterns: {len(unique_raw_texts)}")
output.append("")

for i, pattern in enumerate(sorted(unique_raw_texts), 1):
    output.append(f"{i}. {pattern}")

# Write to file
with open('data/all_raw_effects_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Found {len(all_raw_texts)} abilities with raw_text")
print(f"Found {len(unique_raw_texts)} unique raw_text patterns")
print(f"Output written to data/all_raw_effects_analysis.txt")
