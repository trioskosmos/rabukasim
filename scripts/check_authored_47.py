#!/usr/bin/env python3
"""Check authored frames for card 47"""
import json

with open('data/ability_frame_source_authored.json', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('abilities', [])
for ability in abilities:
    cards = ability.get('cards', [])
    for card in cards:
        if 'PL!-bp3-024-L' in card or '夏色えがおで1,2,Jump!' in card:
            print("Found in authored frames:")
            print(f"Cards: {cards}")
            frames = ability.get('frames', [])
            print(f"Number of frames: {len(frames)}")
            for j, frame in enumerate(frames[:20]):
                print(f"Frame {j}: {frame}")
            break
