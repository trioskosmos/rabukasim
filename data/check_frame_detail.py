#!/usr/bin/env python3
"""Check the compiled frame for PL!S-bp5-009-P."""
import json

with open('cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find the card
card_ids = [cid for cid, card in data['member_db'].items() if card.get('card_no') == 'PL!S-bp5-009-P']
if card_ids:
    card = data['member_db'][card_ids[0]]
    abilities = card.get('abilities', [])
    if abilities:
        ab = abilities[0]
        fp = ab.get('frame_program', {})
        frames = fp.get('frames', [])
        print(f"Found {len(frames)} frames for PL!S-bp5-009-P")
        for i, frame in enumerate(frames):
            print(f"\n  Frame {i}:")
            print(f"    op: {frame.get('op')}")
            attr = frame.get('attr', {})
            if attr:
                print(f"    attr: {attr}")
else:
    print("Card not found")
