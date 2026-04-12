#!/usr/bin/env python3
"""
Count how many abilities are missing frame_verification
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    frame_data = json.load(f)

missing = []
for i, ability in enumerate(frame_data['abilities']):
    if 'frame_verification' not in ability:
        missing.append(i)

print(f"Total abilities: {len(frame_data['abilities'])}")
print(f"Missing frame_verification: {len(missing)}")
print(f"With frame_verification: {len(frame_data['abilities']) - len(missing)}")

if missing:
    print(f"\nMissing verification (first 20): {missing[:20]}")
