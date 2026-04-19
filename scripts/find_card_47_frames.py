#!/usr/bin/env python3
"""Find card 47 frames in ability_frame_source.json"""
import json

with open('data/ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('abilities', [])
for i, ability in enumerate(abilities):
    cards = ability.get('cards', [])
    for card in cards:
        if 'PL!-bp3-024-L' in card or '47' in card:
            print(f"Index {i}: {card}")
            print(json.dumps(ability, ensure_ascii=False, indent=2))
            print()
