#!/usr/bin/env python3
"""Find what the compiled IDs are for specific cards."""
import json

with open('cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Search for "徒町小鈴" or "徒町 小鈴"
search_names = ['徒町小鈴', '徒町 小鈴', 'Tsujicho Kosuzu']

print("Searching for 徒町 小鈴 cards:")
found = False
for cid, card in data['member_db'].items():
    card_name = card.get('name')
    card_no = card.get('card_no')
    if any(search_name.lower() in str(card_name).lower() for search_name in search_names):
        print(f"  ID: {cid}, Card No: {card_no}, Name: {card_name}")
        found = True

if not found:
    print("  NOT FOUND")

# Also try with Komachi character
print("\nSearching for Komachi-related cards:")
for cid, card in list(data['member_db'].items())[:10]:
    card_no = card.get('card_no')
    if 'bp1-013' in str(card_no):
        print(f"  {card_no}: {card.get('name')}")

# Find what logical_id 1050 is
print(f"\nWhat's at ID 1050 (hex: {hex(1050)}):")
if '1050' in data['member_db']:
    card = data['member_db']['1050']
    print(f"  Card No: {card.get('card_no')}, Name: {card.get('name')}")
