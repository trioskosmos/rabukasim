#!/usr/bin/env python3
"""
Fix the last unsupported frame operation: JUMP_IF_NOT_IN_SET
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find and fix JUMP_IF_NOT_IN_SET
for i, ability in enumerate(data['abilities']):
    if 'frames' not in ability:
        continue
    
    frames = ability['frames']
    for frame in frames:
        if frame.get('op') == 'JUMP_IF_NOT_IN_SET':
            # Replace with JUMP_IF_FALSE
            frame['op'] = 'JUMP_IF_FALSE'
            print(f"Ability {i}: Replaced 'JUMP_IF_NOT_IN_SET' with 'JUMP_IF_FALSE'")

# Save the updated data
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed JUMP_IF_NOT_IN_SET operation")
