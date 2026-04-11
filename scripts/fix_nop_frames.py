#!/usr/bin/env python3
"""
Fix common NOP frame issues
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Load semantic dump for reference
with open('data/ability_semantic_dump.json', 'r', encoding='utf-8') as f:
    semantic_data = json.load(f)

# Create a mapping of ability_index to semantic data
semantic_map = {ability['ability_index']: ability for ability in semantic_data['abilities']}

fixed_count = 0

for i, ability in enumerate(data['abilities']):
    if 'frames' not in ability:
        continue
    
    frames = ability['frames']
    semantic_ability = semantic_map[i]
    
    # Fix NOP at the end of frames (should be RETURN)
    if frames and frames[-1].get('op') == 'NOP':
        frames[-1]['op'] = 'RETURN'
        print(f"Ability {i}: Replaced NOP at end with RETURN")
        fixed_count += 1
        continue
    
    # Fix NOP frames that are GROUP_FILTER checks
    text = semantic_ability['primary_text_jp']
    for j, frame in enumerate(frames):
        if frame.get('op') == 'NOP':
            # Check if text mentions group or specific conditions
            if '蓮ノ空' in text and '手札に加えた場合' in text:
                frame['op'] = 'GROUP_FILTER'
                frame['attr'] = {'group_enabled': 1, 'group_id': 'HASUNOSORA'}
                print(f"Ability {i}: Replaced NOP with GROUP_FILTER for Hasunosora")
                fixed_count += 1
            elif 'Aqours' in text and '手札に加えた場合' in text:
                frame['op'] = 'GROUP_FILTER'
                frame['attr'] = {'group_enabled': 1, 'group_id': 'AQOURS'}
                print(f"Ability {i}: Replaced NOP with GROUP_FILTER for Aqours")
                fixed_count += 1
            else:
                # Default to RETURN for unknown NOP
                frame['op'] = 'RETURN'
                print(f"Ability {i}: Replaced NOP with RETURN (default)")
                fixed_count += 1

# Re-index all frames
for i, ability in enumerate(data['abilities']):
    if 'frames' in ability:
        for idx, frame in enumerate(ability['frames']):
            frame['frame_index'] = idx

# Save the updated data
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nFixed {fixed_count} NOP frames")
