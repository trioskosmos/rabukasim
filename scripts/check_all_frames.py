#!/usr/bin/env python3
"""
Check all frames from ability 0 to end for correctness
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

# Common issues to check for
issues = {
    'missing_frames': [],
    'only_return': [],
    'nop_frames': [],
    'missing_jumps': [],
    'incomplete_sequences': [],
    'missing_verification': []
}

# Check each ability
for i, ability in enumerate(frame_data['abilities']):
    frames = ability.get('frames', [])
    
    # Check for missing frames
    if not frames:
        issues['missing_frames'].append(i)
        continue
    
    # Check for only RETURN frame
    if len(frames) == 1 and frames[0].get('op') == 'RETURN':
        issues['only_return'].append(i)
        continue
    
    # Check for NOP frames (except META_RULE which is valid)
    for frame in frames:
        if frame.get('op') == 'NOP' and frame.get('op') != 'META_RULE':
            issues['nop_frames'].append(i)
            break
    
    # Check for JUMP_IF_FALSE without proper preceding condition
    for j, frame in enumerate(frames):
        if frame.get('op') == 'JUMP_IF_FALSE':
            if j == 0:
                issues['missing_jumps'].append(i)
                break
    
    # Check for incomplete sequences (e.g., SELECT without following operation)
    for j, frame in enumerate(frames):
        op = frame.get('op')
        if op in ['SELECT_CARDS', 'SELECT_MEMBER', 'SELECT_LIVE']:
            # Check if there's a following operation that uses the selection
            if j == len(frames) - 1:
                issues['incomplete_sequences'].append(i)
                break
    
    # Check for missing frame_verification
    if 'frame_verification' not in ability:
        issues['missing_verification'].append(i)

# Print results
print(f"Total abilities: {len(frame_data['abilities'])}")
print(f"\nIssues found:")
print(f"  Missing frames: {len(issues['missing_frames'])}")
print(f"  Only RETURN frame: {len(issues['only_return'])}")
print(f"  NOP frames: {len(issues['nop_frames'])}")
print(f"  Missing jumps: {len(issues['missing_jumps'])}")
print(f"  Incomplete sequences: {len(issues['incomplete_sequences'])}")
print(f"  Missing verification: {len(issues['missing_verification'])}")

# Print details for each issue type
if issues['missing_frames']:
    print(f"\nMissing frames (abilities: {issues['missing_frames'][:20]}...)")
if issues['only_return']:
    print(f"\nOnly RETURN frame (abilities: {issues['only_return'][:20]}...)")
if issues['nop_frames']:
    print(f"\nNOP frames (abilities: {issues['nop_frames'][:20]}...)")
if issues['missing_jumps']:
    print(f"\nMissing jumps (abilities: {issues['missing_jumps'][:20]}...)")
if issues['incomplete_sequences']:
    print(f"\nIncomplete sequences (abilities: {issues['incomplete_sequences'][:20]}...)")
if issues['missing_verification']:
    print(f"\nMissing verification (abilities: {issues['missing_verification'][:20]}...)")

total_issues = sum(len(v) for v in issues.values())
print(f"\nTotal issues: {total_issues}")
