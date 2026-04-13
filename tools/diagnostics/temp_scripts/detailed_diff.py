#!/usr/bin/env python3
"""Detailed diff analysis between two ability sources."""

import json
from collections import defaultdict

def load_abilities(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load both files
original = load_abilities('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json')
from_cards = load_abilities('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_from_cards.json')

# Build lookup by text
orig_by_text = {}
for a in original['abilities']:
    text = a['source_ability_texts'][0]['jp']
    orig_by_text[text] = a

cards_by_text = {}
for a in from_cards['abilities']:
    text = a['source_ability_texts'][0]['jp']
    cards_by_text[text] = a

# Find differences
only_in_original = []
only_in_cards = []
trigger_diffs = []

for text, ability in orig_by_text.items():
    if text not in cards_by_text:
        only_in_original.append((text[:100], ability['trigger']))

for text, ability in cards_by_text.items():
    if text not in orig_by_text:
        only_in_cards.append((text[:100], ability['trigger']))
    else:
        orig_trigger = orig_by_text[text]['trigger']
        cards_trigger = ability['trigger']
        if orig_trigger != cards_trigger:
            trigger_diffs.append((text[:80], orig_trigger, cards_trigger))

print("=" * 60)
print("ONLY IN ORIGINAL (ability_frame_source.json)")
print(f"Count: {len(only_in_original)}")
print("-" * 60)
for text, trigger in only_in_original[:10]:
    print(f"[{trigger}] {text}...")
print()

print("=" * 60)
print("ONLY IN CARDS.JSON MODE")
print(f"Count: {len(only_in_cards)}")
print("-" * 60)
for text, trigger in only_in_cards[:10]:
    print(f"[{trigger}] {text}...")
print()

print("=" * 60)
print("TRIGGER DIFFERENCES")
print(f"Count: {len(trigger_diffs)}")
print("-" * 60)
for text, orig_trig, cards_trig in trigger_diffs[:10]:
    print(f"{orig_trig} -> {cards_trig}: {text}...")
print()

# Summary stats
print("=" * 60)
print("SUMMARY")
print(f"Original total: {len(original['abilities'])}")
print(f"Cards mode total: {len(from_cards['abilities'])}")
print(f"Common: {len(set(orig_by_text.keys()) & set(cards_by_text.keys()))}")
print(f"Only in original: {len(only_in_original)}")
print(f"Only in cards: {len(only_in_cards)}")
print(f"Trigger mismatches: {len(trigger_diffs)}")
