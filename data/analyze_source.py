#!/usr/bin/env python3
"""Analyze cards.json to see how many items and of what types."""
import json

with open('cards.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

print(f"Total items in cards.json: {len(raw_data)}")

# Count by type
type_counts = {}
for key, item in raw_data.items():
    ctype = item.get("type", "UNKNOWN")
    if ctype not in type_counts:
        type_counts[ctype] = 0
    type_counts[ctype] += 1

print(f"\nCards by type:")
for ctype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {ctype}: {count}")

# Look for specific test cards
test_cards = ['PL!SP-sd1-001-SD', 'PL!S-1-001-P', 'PL!S-bp1-001-P']
print(f"\nLooking for test cards:")
for card_no in test_cards:
    if card_no in raw_data:
        item = raw_data[card_no]
        print(f"  {card_no}: Found (type={item.get('type')})")
    else:
        print(f"  {card_no}: NOT FOUND")

# Show totals
print(f"\nMember cards (type='メンバー'): {type_counts.get('メンバー', 0)}")
print(f"Live cards (type='ライブ'): {type_counts.get('ライブ', 0)}")
