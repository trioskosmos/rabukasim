#!/usr/bin/env python3
"""Check what group IDs μ's members have in the card database"""
import json

with open('data/cards_compiled.json', encoding='utf-8') as f:
    compiled = json.load(f)

member_db = compiled.get('member_db', {})

# Find μ's members
mus_members = []
for card_id, card in member_db.items():
    groups = card.get('groups', [])
    if 0 in groups:  # μ's group ID is 0
        mus_members.append({
            'card_id': card_id,
            'name': card.get('name', ''),
            'groups': groups
        })

print(f"Found {len(mus_members)} μ's members (group 0)")
for member in mus_members[:10]:
    print(f"  {member['card_id']}: {member['name']} - groups: {member['groups']}")
