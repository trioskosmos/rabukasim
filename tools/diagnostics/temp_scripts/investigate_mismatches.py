#!/usr/bin/env python3
"""Investigate trigger mismatches and slash-separated triggers."""

import json

def load_abilities(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

original = load_abilities('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json')
from_cards = load_abilities('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_from_cards.json')

# Build lookup
orig_by_text = {}
for a in original['abilities']:
    text = a['source_ability_texts'][0]['jp']
    orig_by_text[text] = a

cards_by_text = {}
for a in from_cards['abilities']:
    text = a['source_ability_texts'][0]['jp']
    cards_by_text[text] = a

# Find trigger mismatches
print("=" * 60)
print("TRIGGER MISMATCHES (same text, different triggers)")
print("=" * 60)
for text in set(orig_by_text.keys()) & set(cards_by_text.keys()):
    orig_trigger = orig_by_text[text]['trigger']
    cards_trigger = cards_by_text[text]['trigger']
    if orig_trigger != cards_trigger:
        print(f"\nOriginal: {orig_trigger}")
        print(f"Cards:    {cards_trigger}")
        print(f"Text:     {text[:150]}...")
        print(f"Cards:    {cards_by_text[text]['source_ability_texts'][0]['cards'][:3]}")

# Find slash-separated triggers
print("\n" + "=" * 60)
print("SLASH-SEPARATED TRIGGERS (trigger1/trigger2)")
print("=" * 60)
slash_count = 0
for text, ability in orig_by_text.items():
    if '/' in text and any(icon in text for icon in ['toujyou', 'kidou', 'jidou', 'jyouji', 'live_start']):
        slash_count += 1
        if slash_count <= 5:
            print(f"\nTrigger: {ability['trigger']}")
            print(f"Text: {text[:200]}...")
            parts = text.split('/')
            for i, part in enumerate(parts):
                print(f"  [{i+1}] {part[:80]}...")

print(f"\nTotal slash-separated: {slash_count}")
