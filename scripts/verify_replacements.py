#!/usr/bin/env python3
"""
Verify that the frame operation replacements are semantically correct
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

# Abilities where I made replacements that need verification
# These are the abilities that had unsupported operations that I replaced
replacement_abilities = [6, 58, 59, 60, 354, 401, 408, 409, 410, 418, 421, 439, 443, 445, 446, 452, 454, 456, 460, 461, 468, 469, 470, 471, 472, 475, 480, 484, 485, 492, 495, 501, 505, 506, 509, 516, 521, 524, 526, 543, 556, 577, 593, 594, 596, 610, 611]

print("Verifying frame operation replacements against semantic text:\n")

for i in replacement_abilities:
    frame_ability = frame_data['abilities'][i]
    semantic_ability = semantic_map[i]
    
    print(f"\n{'='*80}")
    print(f"Ability {i}: {semantic_ability['trigger']}")
    print(f"Text: {semantic_ability['primary_text_jp']}")
    print(f"\nCurrent frames:")
    for frame in frame_ability.get('frames', []):
        print(f"  Frame {frame['frame_index']}: {frame['op']}")
        if 'attr' in frame:
            print(f"    attr: {frame['attr']}")
        if 'params' in frame and frame['params']:
            print(f"    params: {frame['params']}")
