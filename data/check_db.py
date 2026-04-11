#!/usr/bin/env python3
"""Check compiled card database."""
import json

with open('cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Keys in cards_compiled.json: {list(data.keys())}")
member_db = data.get('member_db', {})
live_db = data.get('live_db', {})
energy_db = data.get('energy_db', {})

print(f"Member DB type: {type(member_db)}, size: {len(member_db)}")
print(f"Live DB type: {type(live_db)}, size: {len(live_db)}")
print(f"Energy DB type: {type(energy_db)}, size: {len(energy_db)}")

# Check first few member IDs
if isinstance(member_db, dict):
    first_keys = list(member_db.keys())[:10]
    print(f"\nFirst 10 member DB keys: {first_keys}")
    
    # Look for specific cards
    search_cards = ['PL!SP-sd1-001-SD', 'PL!S-1-001-P', 'PL!S-bp1-001-P']
    print(f"\nSearching for cards: {search_cards}")
    for key, member in member_db.items():
        card_no = member.get('card_no')
        if card_no in search_cards:
            print(f"Found card: {card_no} (key: {key})")
            print(f"  Name: {member.get('name_jp')}")
            print(f"  Abilities: {len(member.get('abilities', []))}")
