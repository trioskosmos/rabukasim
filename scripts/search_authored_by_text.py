#!/usr/bin/env python3
"""Search authored frames by ability text"""
import json

with open('data/ability_frame_source_authored.json', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('abilities', [])
for ability in abilities:
    full_text = ability.get('full_text', '')
    if 'heart01' in full_text and 'heart06' in full_text:
        print("Found in authored frames:")
        print(f"Cards: {ability.get('cards', [])}")
        print(f"Full text: {full_text[:200]}")
        frames = ability.get('frames', [])
        print(f"Number of frames: {len(frames)}")
        for j, frame in enumerate(frames[:10]):
            print(f"  Frame {j}: {frame}")
        print()
