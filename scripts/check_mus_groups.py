#!/usr/bin/env python3
"""Check groups for μ's cards"""
import json

with open('data/cards.json', encoding='utf-8') as f:
    data = json.load(f)

mus_cards = []
for k, v in data.items():
    name = v.get('name', '')
    if 'mu' in name.lower() or 'μ' in name:
        mus_cards.append((k, v))

print(f'Found {len(mus_cards)} μs cards')
if mus_cards:
    for k, v in mus_cards[:10]:
        print(f"ID: {k}, Name: {v.get('name')}, Groups: {v.get('groups', [])}")
