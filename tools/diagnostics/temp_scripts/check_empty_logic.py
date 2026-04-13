#!/usr/bin/env python3
"""Analyze abilities with empty logic - what's not being extracted at all."""

import json

with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

empty_abilities = []

for ability in data['abilities']:
    source = ability['source_ability_texts'][0]
    logic = source['logic']
    jp = source['jp']
    cards = source['cards']
    
    if not logic or not logic.strip():
        empty_abilities.append({
            'card': cards[0] if cards else 'UNKNOWN',
            'jp': jp[:200],
            'trigger': ability['trigger'],
            'jp_length': len(jp)
        })

print("=" * 70)
print(f"ABILITIES WITH EMPTY LOGIC ({len(empty_abilities)} found)")
print("=" * 70)

for i, ability in enumerate(empty_abilities, 1):
    print(f"\n{i}. {ability['card']}")
    print(f"   Trigger: {ability['trigger']}")
    print(f"   JP Length: {ability['jp_length']} chars")
    print(f"   JP: {ability['jp']}...")
    print("-" * 70)

# Analysis
print("\n" + "=" * 70)
print("ANALYSIS: WHY ARE THESE EMPTY?")
print("=" * 70)

# By trigger
by_trigger = {}
for ability in empty_abilities:
    t = ability['trigger']
    by_trigger[t] = by_trigger.get(t, 0) + 1

print("\nBy Trigger:")
for t, count in sorted(by_trigger.items(), key=lambda x: x[1], reverse=True):
    print(f"  {count}x {t}")

# Check if they're all trigger-only (short JP text)
short_count = sum(1 for a in empty_abilities if a['jp_length'] < 50)
print(f"\nShort text (<50 chars, likely trigger-only): {short_count}/{len(empty_abilities)}")

# Sample JP text patterns
print("\nSample JP text patterns:")
for ability in empty_abilities[:3]:
    print(f"  {ability['jp'][:80]}...")
