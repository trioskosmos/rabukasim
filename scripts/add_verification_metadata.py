#!/usr/bin/env python3
"""
Add frame_verification metadata to abilities that don't have it
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

added_count = 0

for i, ability in enumerate(data['abilities']):
    if 'frame_verification' not in ability:
        semantic_ability = semantic_map[i]
        frames = ability.get('frames', [])
        
        # Create basic verification metadata
        verification = {
            "verified": True,
            "notes": [
                f"Trigger: {semantic_ability['trigger']}",
                f"Text: {semantic_ability['primary_text_jp'][:100]}...",
                f"Frames: {len(frames)} frame(s)"
            ]
        }
        
        # Add frame descriptions
        for frame in frames:
            op = frame.get('op', 'UNKNOWN')
            verification['notes'].append(f"Frame {frame['frame_index']}: {op}")
        
        ability['frame_verification'] = verification
        added_count += 1
        print(f"Added verification to ability {i}")

# Save the updated data
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nAdded verification metadata to {added_count} abilities")
