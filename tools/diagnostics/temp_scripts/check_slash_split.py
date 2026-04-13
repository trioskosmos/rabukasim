#!/usr/bin/env python3
"""Check how slash-separated triggers are being split."""

import json

with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find abilities that came from slash-separated triggers
# These will have a trigger icon at the start but no "/" in the text
slash_sources = []
for ability in data['abilities']:
    jp = ability['source_ability_texts'][0]['jp']
    cards = ability['source_ability_texts'][0]['cards']
    trigger = ability['trigger']
    
    # Look for abilities that are likely from slash split
    # They start with trigger icon and contain effect text
    if jp.startswith('{{toujyou.png') or jp.startswith('{{live_start.png') or jp.startswith('{{kidou.png'):
        if len(cards) > 0:
            slash_sources.append({
                'trigger': trigger,
                'jp': jp[:120],
                'cards': cards[:3],  # Show first 3 cards
                'card_count': len(cards)
            })

# Show some examples
print("=== SLASH-SPLIT ABILITY EXAMPLES ===")
print(f"Total abilities with trigger icons at start: {len(slash_sources)}\n")

# Group by trigger to show variety
by_trigger = {}
for item in slash_sources:
    t = item['trigger']
    if t not in by_trigger:
        by_trigger[t] = []
    by_trigger[t].append(item)

for trigger, items in by_trigger.items():
    print(f"\n--- Trigger: {trigger} ({len(items)} abilities) ---")
    for item in items[:2]:  # Show 2 per trigger
        print(f"  JP: {item['jp']}...")
        print(f"  Cards ({item['card_count']} total): {item['cards']}")
        print()
