#!/usr/bin/env python3
"""
Review abilities 401-450 from frame source
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

# Review abilities 401-450
issues = []
for i in range(401, 451):
    if i >= len(frame_data['abilities']):
        issues.append(f"Ability {i}: Missing from frame source")
        continue
    
    frame_ability = frame_data['abilities'][i]
    semantic_ability = semantic_map.get(i)
    
    if not semantic_ability:
        issues.append(f"Ability {i}: Missing from semantic dump")
        continue
    
    # Check if frames exist
    if not frame_ability.get('frames'):
        issues.append(f"Ability {i}: No frames defined")
        continue
    
    # Check frame_verification
    verification = frame_ability.get('frame_verification', {})
    if not verification.get('verified'):
        issues.append(f"Ability {i}: Not verified")
        continue
    
    # Print summary of verified abilities
    print(f"Ability {i}: {semantic_ability['trigger']} - VERIFIED")

print(f"\n\nTotal issues found: {len(issues)}")
for issue in issues:
    print(f"  - {issue}")
