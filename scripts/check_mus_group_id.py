#!/usr/bin/env python3
"""Check group ID for μ's members"""
import json

with open('data/cards_compiled.json', encoding='utf-8') as f:
    data = json.load(f)

member_db = data.get('member_db', {})
mus_members = []
for k, v in member_db.items():
    name = v.get('name', '')
    if 'mu' in name.lower() or 'μ' in name:
        mus_members.append((k, v))

print(f'Found {len(mus_members)} μs members')
if mus_members:
    for k, v in mus_members[:5]:
        print(f"ID: {k}, Name: {v.get('name')}, Groups: {v.get('groups', [])}")
