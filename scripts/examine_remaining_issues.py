#!/usr/bin/env python3
"""
Examine abilities with remaining issues
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    frame_data = json.load(f)

# Load semantic dump for reference
with open('data/ability_semantic_dump.json', 'r', encoding='utf-8') as f:
    semantic_data = json.load(f)

# Create a mapping of ability_index to semantic data
semantic_map = {ability['ability_index']: ability for ability in semantic_data['abilities']}

# Abilities with only RETURN frame
only_return = [470, 505, 506]

# Abilities with missing jumps
missing_jumps = [446, 468, 492, 595]

print("=== Abilities with only RETURN frame ===")
for i in only_return:
    frame_ability = frame_data['abilities'][i]
    semantic_ability = semantic_map[i]
    
    print(f"\nAbility {i}: {semantic_ability['trigger']}")
    print(f"Text: {semantic_ability['primary_text_jp']}")
    print(f"Current frames: {len(frame_ability.get('frames', []))}")
    for frame in frame_ability.get('frames', []):
        print(f"  Frame {frame['frame_index']}: {frame['op']}")

print("\n\n=== Abilities with missing jumps ===")
for i in missing_jumps:
    frame_ability = frame_data['abilities'][i]
    semantic_ability = semantic_map[i]
    
    print(f"\nAbility {i}: {semantic_ability['trigger']}")
    print(f"Text: {semantic_ability['primary_text_jp']}")
    print(f"Current frames: {len(frame_ability.get('frames', []))}")
    for frame in frame_ability.get('frames', []):
        print(f"  Frame {frame['frame_index']}: {frame['op']}")
