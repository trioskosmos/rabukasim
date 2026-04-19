#!/usr/bin/env python3
"""List all cards in frame source"""
import json

with open('data/ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('abilities', [])
print(f"Total abilities in frame source: {len(abilities)}")

for i, ability in enumerate(abilities[:10]):
    cards = ability.get('cards', [])
    print(f"{i}: {cards}")
