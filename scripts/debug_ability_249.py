#!/usr/bin/env python3
"""
Debug ability 249 to understand the discrepancy
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    frame_source = json.load(f)

# Check ability 249
ability_249 = frame_source['abilities'][249]
print(f"Ability 249 text: {ability_249.get('primary_text_jp', '')}")
print(f"\nFrames in ability 249:")
for frame in ability_249.get('frames', []):
    print(f"  Frame {frame['frame_index']}: {frame['op']}")

# Check if there are multiple abilities with the same text
print(f"\nSearching for abilities with similar text...")
for i, ability in enumerate(frame_source['abilities']):
    text = ability.get('primary_text_jp', '')
    if 'ライブ開始時手札を2枚控え室に置いてもよい' in text:
        print(f"Ability {i}: {text[:60]}...")
        print(f"  Frames: {[f['op'] for f in ability.get('frames', [])]}")
