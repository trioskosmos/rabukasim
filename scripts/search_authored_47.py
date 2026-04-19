#!/usr/bin/env python3
"""Search authored frames for card 47"""
import json

with open('data/ability_frame_source_authored.json', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('abilities', [])
for i, ability in enumerate(abilities):
    full_text = ability.get('full_text', '')
    if 'heart06' in full_text and 'heart01' in full_text:
        print(f"Authored Index {i}")
        print(f"Cards: {ability.get('cards', [])}")
        print(f"Full text: {full_text[:300]}")
        frames = ability.get('frames', [])
        print(f"Number of frames: {len(frames)}")
        for j, frame in enumerate(frames[:5]):
            print(f"  Frame {j}: {frame}")
        print()
