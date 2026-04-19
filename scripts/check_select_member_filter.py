#!/usr/bin/env python3
"""Check SELECT_MEMBER frame filter in compiled card 47"""
import json

with open('data/cards_compiled.json', encoding='utf-8') as f:
    compiled = json.load(f)

live_db = compiled.get('live_db', {})
card_47 = live_db.get('47')
if card_47:
    abilities = card_47.get('abilities', [])
    for i, ability in enumerate(abilities):
        frames = ability.get('frame_program', {}).get('frames', [])
        print(f"Ability {i}:")
        for j, frame in enumerate(frames):
            if frame.get('op') == 'SELECT_MEMBER':
                print(f"  Frame {j}: SELECT_MEMBER")
                print(f"    attr: {frame.get('attr')}")
                print(f"    slot: {frame.get('slot')}")
