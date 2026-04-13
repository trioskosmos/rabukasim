#!/usr/bin/env python3
"""Analyze abilities with partial logic extraction."""

import json

with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

partial_abilities = []

for ability in data['abilities']:
    source = ability['source_ability_texts'][0]
    logic = source['logic']
    jp = source['jp']
    cards = source['cards']
    
    # Check if it has partial logic
    has_operations = any(kw in logic for kw in ['draw', 'add', 'select', 'discard', 'pay', 'tap', 'if'])
    has_empty_or_garbled = not logic.strip() or len([c for c in logic if ord(c) > 127]) > 5
    
    if has_operations and (has_empty_or_garbled or logic.count('\n') < 2):
        partial_abilities.append({
            'card': cards[0] if cards else 'UNKNOWN',
            'jp': jp[:120],
            'logic': logic[:150],
            'trigger': ability['trigger'],
            'line_count': len(logic.split('\n'))
        })

print("=" * 70)
print(f"ABILITIES WITH PARTIAL LOGIC EXTRACTION ({len(partial_abilities)} found)")
print("=" * 70)

# Show examples
for i, ability in enumerate(partial_abilities[:10], 1):
    print(f"\n{i}. {ability['card']}")
    print(f"   Trigger: {ability['trigger']}")
    print(f"   Lines: {ability['line_count']}")
    print(f"   JP: {ability['jp']}...")
    print(f"   LOGIC: {ability['logic']}...")
    print("-" * 70)

# Analyze common patterns in partial logic
print("\n" + "=" * 70)
print("ANALYSIS: WHAT'S BEING MISSED")
print("=" * 70)

# Count by trigger type
by_trigger = {}
for ability in partial_abilities:
    t = ability['trigger']
    by_trigger[t] = by_trigger.get(t, 0) + 1

print("\nBy Trigger Type:")
for t, count in sorted(by_trigger.items(), key=lambda x: x[1], reverse=True):
    print(f"  {count:3d}x {t}")

# Check for common untranslated fragments
print("\nSample Japanese text from partial abilities:")
for ability in partial_abilities[:5]:
    print(f"  {ability['card']}: {ability['jp'][:60]}...")
