#!/usr/bin/env python3
"""Search authored frames for card 47"""
import json

with open('data/ability_frame_source_authored.json', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('abilities', [])
print(f"Total abilities in authored frames: {len(abilities)}")

for i, ability in enumerate(abilities):
    full_text = ability.get('full_text', '')
    if '夏色えがおで' in full_text or '47' in str(ability.get('cards', [])):
        print(f"Found at index {i}")
        print(f"Cards: {ability.get('cards', [])}")
        print(f"Full text: {full_text[:100]}")
        frames = ability.get('frames', [])
        print(f"Number of frames: {len(frames)}")
        for j, frame in enumerate(frames[:10]):
            print(f"  Frame {j}: {frame.get('op')}")
            if frame.get('op') == 'SELECT_MEMBER':
                print(f"    Attr: {frame.get('attr')}")
        print()
