#!/usr/bin/env python3
"""
Comprehensively verify all frame operation replacements against semantic text
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

# Abilities where I made replacements
replacement_abilities = [6, 58, 59, 60, 354, 401, 408, 409, 410, 418, 421, 439, 443, 445, 446, 452, 454, 456, 460, 461, 468, 469, 470, 471, 472, 475, 480, 484, 485, 492, 495, 501, 505, 506, 509, 516, 521, 524, 526, 543, 556, 577, 593, 594, 596, 610, 611]

issues_found = []

for i in replacement_abilities:
    frame_ability = frame_data['abilities'][i]
    semantic_ability = semantic_map[i]
    text = semantic_ability['primary_text_jp']
    frames = frame_ability.get('frames', [])
    
    # Check for specific issues based on text patterns
    
    # Check if text mentions "手札に加える" (add to hand) but frames don't have ADD_TO_HAND
    if "手札に加える" in text or "手札に加えて" in text:
        has_add_to_hand = any(f.get('op') == 'ADD_TO_HAND' for f in frames)
        if not has_add_to_hand:
            issues_found.append((i, "Text mentions adding to hand but no ADD_TO_HAND frame"))
    
    # Check if text mentions "控え室に置く" (place in discard) but frames don't have MOVE_TO_DISCARD
    if "控え室に置く" in text or "控え室に置いて" in text:
        has_move_to_discard = any(f.get('op') == 'MOVE_TO_DISCARD' for f in frames)
        if not has_move_to_discard:
            issues_found.append((i, "Text mentions placing in discard but no MOVE_TO_DISCARD frame"))
    
    # Check if text mentions "引く" (draw) but frames don't have DRAW
    if "引く" in text and "エール" not in text:  # Exclude yell-related text
        has_draw = any(f.get('op') == 'DRAW' for f in frames)
        if not has_draw:
            issues_found.append((i, "Text mentions draw but no DRAW frame"))
    
    # Check if text mentions "得る" (gain hearts/blades) but frames don't have ADD_HEARTS or ADD_BLADES
    if "得る" in text:
        has_add = any(f.get('op') in ['ADD_HEARTS', 'ADD_BLADES'] for f in frames)
        if not has_add:
            issues_found.append((i, "Text mentions gaining but no ADD_HEARTS/ADD_BLADES frame"))

print("Semantic verification issues found:\n")
for ability_id, reason in issues_found:
    print(f"Ability {ability_id}: {reason}")
    semantic_ability = semantic_map[ability_id]
    print(f"  Text: {semantic_ability['primary_text_jp'][:80]}...")
    print()

print(f"Total issues: {len(issues_found)}")
