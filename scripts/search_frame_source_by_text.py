#!/usr/bin/env python3
"""Search frame source by ability text"""
import json

with open('data/ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('abilities', [])
for ability in abilities:
    full_text = ability.get('full_text', '')
    if 'heart01' in full_text and 'heart06' in full_text and 'μ' in full_text:
        print("Found in frame source:")
        print(f"Cards: {ability.get('cards', [])}")
        frames = ability.get('frames', [])
        print(f"Number of frames: {len(frames)}")
        for j, frame in enumerate(frames[:20]):
            if frame.get('op') == 'SELECT_MEMBER':
                print(f"Frame {j}: SELECT_MEMBER - {frame}")
            else:
                print(f"Frame {j}: {frame.get('op')}")
        print()
