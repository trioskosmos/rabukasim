#!/usr/bin/env python3
"""
Examine abilities with NOP frames to determine what they should be
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

# Abilities with NOP frames
nop_abilities = [34, 64, 82, 90, 115, 139, 154, 198, 207, 212, 219, 227, 237, 238, 239, 254, 255, 258, 259, 273, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 318, 319, 320, 321, 322]

for i in nop_abilities:
    frame_ability = frame_data['abilities'][i]
    semantic_ability = semantic_map[i]
    
    print(f"\n{'='*80}")
    print(f"Ability {i}: {semantic_ability['trigger']}")
    print(f"Text: {semantic_ability['primary_text_jp']}")
    print(f"\nCurrent frames:")
    for frame in frame_ability.get('frames', []):
        print(f"  Frame {frame['frame_index']}: {frame['op']}")
