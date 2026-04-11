#!/usr/bin/env python3
"""
Examine abilities with semantic verification issues
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

# Abilities with semantic issues
issue_abilities = [439, 501, 516, 524, 526]

for i in issue_abilities:
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
