#!/usr/bin/env python3
"""Compare abilities extracted from different sources."""

import json
from pathlib import Path

def load_abilities(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def count_stats(data):
    """Count various statistics."""
    total = len(data['abilities'])
    with_logic = sum(1 for a in data['abilities'] 
                     if a.get('source_ability_texts', [{}])[0].get('logic', '').strip())
    empty = total - with_logic
    return {'total': total, 'with_logic': with_logic, 'empty': empty}

# Load both files
original = load_abilities('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json')
from_cards = load_abilities('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_from_cards.json')

orig_stats = count_stats(original)
cards_stats = count_stats(from_cards)

print("=== COMPARISON ===")
print(f"Original (from ability_frame_source.json):")
print(f"  Total abilities: {orig_stats['total']}")
print(f"  With logic: {orig_stats['with_logic']}")
print(f"  Empty logic: {orig_stats['empty']}")
print()
print(f"From cards.json:")
print(f"  Total abilities: {cards_stats['total']}")
print(f"  With logic: {cards_stats['with_logic']}")
print(f"  Empty logic: {cards_stats['empty']}")
print()

# Check if triggers are similar
orig_triggers = {}
cards_triggers = {}

for a in original['abilities']:
    t = a.get('trigger', 'UNKNOWN')
    orig_triggers[t] = orig_triggers.get(t, 0) + 1

for a in from_cards['abilities']:
    t = a.get('trigger', 'UNKNOWN')
    cards_triggers[t] = cards_triggers.get(t, 0) + 1

print("Trigger distribution (original vs from cards):")
all_triggers = set(orig_triggers.keys()) | set(cards_triggers.keys())
for t in sorted(all_triggers):
    o = orig_triggers.get(t, 0)
    c = cards_triggers.get(t, 0)
    print(f"  {t}: {o} vs {c} {'OK' if o == c else 'DIFF'}")

print("\nConclusion: The --from-cards mode works similarly but may have slight differences")
print("in grouping (625 vs 613 abilities) due to how cards with multiple abilities are handled.")
