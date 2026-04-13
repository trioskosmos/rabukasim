#!/usr/bin/env python3
"""Simple summary of extraction coverage."""

import json
import re

with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Count abilities by logic quality
categories = {
    'full_logic': [],      # Has complete logic
    'partial_logic': [],   # Has some logic but also empty/japanese
    'empty_logic': [],     # Empty logic field
    'trigger_only': []      # Just trigger icon, no effect
}

for ability in data['abilities']:
    source = ability['source_ability_texts'][0]
    logic = source['logic']
    jp = source['jp']
    cards = source['cards']
    
    if not logic or not logic.strip():
        categories['empty_logic'].append(cards[0] if cards else 'UNKNOWN')
    elif logic.strip().startswith('{{') and len(logic.strip().split('\n')) == 1:
        categories['trigger_only'].append(cards[0] if cards else 'UNKNOWN')
    elif 'if' in logic or 'add' in logic or 'draw' in logic or 'select' in logic:
        # Has actual operations
        categories['full_logic'].append(cards[0] if cards else 'UNKNOWN')
    else:
        categories['partial_logic'].append(cards[0] if cards else 'UNKNOWN')

print("=" * 60)
print("EXTRACTION COVERAGE SUMMARY")
print("=" * 60)
print(f"\nTotal abilities: {len(data['abilities'])}\n")

print(f"[OK] Full logic extracted:   {len(categories['full_logic']):3d} ({len(categories['full_logic'])/len(data['abilities'])*100:.1f}%)")
print(f"[~]  Partial logic:          {len(categories['partial_logic']):3d} ({len(categories['partial_logic'])/len(data['abilities'])*100:.1f}%)")
print(f"[X]  Empty logic:            {len(categories['empty_logic']):3d} ({len(categories['empty_logic'])/len(data['abilities'])*100:.1f}%)")
print(f"[!]  Trigger only:           {len(categories['trigger_only']):3d} ({len(categories['trigger_only'])/len(data['abilities'])*100:.1f}%)")

# Show sample cards from each category
print("\n" + "=" * 60)
print("SAMPLE CARDS BY CATEGORY")
print("=" * 60)

for cat_name, label in [('full_logic', 'Full Logic'), ('partial_logic', 'Partial Logic'), 
                        ('empty_logic', 'Empty Logic'), ('trigger_only', 'Trigger Only')]:
    cards = categories[cat_name]
    print(f"\n{label} ({len(cards)} cards):")
    for card in cards[:3]:
        print(f"  - {card}")
    if len(cards) > 3:
        print(f"  ... and {len(cards) - 3} more")

# Count logic operations
print("\n" + "=" * 60)
print("MOST COMMON LOGIC OPERATIONS")
print("=" * 60)

operation_counts = {}
for ability in data['abilities']:
    logic = ability['source_ability_texts'][0]['logic']
    for line in logic.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Categorize by first word
        first_word = line.split()[0] if line.split() else 'unknown'
        operation_counts[first_word] = operation_counts.get(first_word, 0) + 1

sorted_ops = sorted(operation_counts.items(), key=lambda x: x[1], reverse=True)
for op, count in sorted_ops[:15]:
    print(f"  {count:4d}x {op}")
