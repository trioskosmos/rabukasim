#!/usr/bin/env python3
"""
Examine detailed info for abilities 576, 577
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load both files
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    frame_data = json.load(f)

with open('data/ability_semantic_dump.json', 'r', encoding='utf-8') as f:
    semantic_data = json.load(f)

# Create a mapping of ability_index to semantic data
semantic_map = {ability['ability_index']: ability for ability in semantic_data['abilities']}

# Examine abilities in detail
for i in [576, 577]:
    frame_ability = frame_data['abilities'][i]
    semantic_ability = semantic_map[i]
    
    print(f"\n{'='*80}")
    print(f"Ability {i}: {semantic_ability['trigger']}")
    print(f"Text: {semantic_ability['primary_text_jp']}")
    print(f"\nCurrent frames:")
    for frame in frame_ability.get('frames', []):
        print(f"  Frame {frame['frame_index']}: {frame['op']}")
        print(f"    {json.dumps(frame, ensure_ascii=False)}")
