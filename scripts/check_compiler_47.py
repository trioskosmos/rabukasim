#!/usr/bin/env python3
"""Check how compiler resolves card 47"""
import json

# Check if card is in frame source
with open('data/ability_frame_source.json', encoding='utf-8') as f:
    frame_source = json.load(f)

abilities = frame_source.get('abilities', [])
found_in_frame_source = any('47' in str(a.get('cards', [])) for a in abilities)
print(f"Card 47 in frame source: {found_in_frame_source}")

# Check if card is in authored frames
with open('data/ability_frame_source_authored.json', encoding='utf-8') as f:
    authored = json.load(f)

abilities = authored.get('abilities', [])
found_in_authored = any('47' in str(a.get('cards', [])) for a in abilities)
print(f"Card 47 in authored frames: {found_in_authored}")

# Check compiled cards
with open('data/cards_compiled.json', encoding='utf-8') as f:
    compiled = json.load(f)

live_db = compiled.get('live_db', {})
card_47 = live_db.get('47')
if card_47:
    print(f"Card 47 in compiled cards: Yes")
    print(f"Number of abilities: {len(card_47.get('abilities', []))}")
    for i, ab in enumerate(card_47.get('abilities', [])):
        frames = ab.get('frame_program', {}).get('frames', [])
        select_member_frames = [f for f in frames if f.get('op') == 'SELECT_MEMBER']
        print(f"  Ability {i}: {len(frames)} frames, {len(select_member_frames)} SELECT_MEMBER frames")
        if select_member_frames:
            for sm in select_member_frames:
                print(f"    SELECT_MEMBER attr: {sm.get('attr')}")
