#!/usr/bin/env python3
"""Check if cards exist in the compiled database."""
import json

with open('cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check for specific card_nos
test_card_nos = ['PL!S-bp2-004-P']

for card_no in test_card_nos:
    card_ids = [cid for cid, card in data['member_db'].items() if card.get('card_no') == card_no]
    if card_ids:
        print(f"{card_no}: ID={card_ids[0]}")
        card = data['member_db'][card_ids[0]]
        abilities = card.get('abilities', [])
        print(f"  Abilities: {len(abilities)}")
        if abilities:
            ab = abilities[0]
            print(f"  Ability keys: {list(ab.keys())}")
            print(f"  frame_program: {ab.get('frame_program')}")
            if ab.get('frame_program'):
                fp = ab['frame_program']
                print(f"  frame_program keys: {list(fp.keys())}")
                frames = fp.get('frames', [])
                print(f"  Frames: {len(frames)}")
                if frames:
                    print(f"  First frame: {frames[0]}")
    else:
        print(f"{card_no}: NOT FOUND")
