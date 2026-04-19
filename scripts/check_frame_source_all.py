#!/usr/bin/env python3
"""Check all cards in frame source"""
import json

with open('data/ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('abilities', [])
print(f"Total abilities in frame source: {len(abilities)}")

for i, ability in enumerate(abilities[:50]):
    cards = ability.get('cards', [])
    if cards:
        print(f"{i}: {cards}")
