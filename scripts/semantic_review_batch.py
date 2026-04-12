#!/usr/bin/env python3
"""
Systematically review abilities for semantic correctness
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

# Review abilities in batches
start = 0
end = 100

issues = []

for i in range(start, end):
    frame_ability = frame_data['abilities'][i]
    semantic_ability = semantic_map[i]
    text = semantic_ability['primary_text_jp']
    frames = frame_ability.get('frames', [])
    
    # Check for common semantic mismatches
    
    # Check if text mentions "手札をX枚控え室に置く" (discard X cards from hand)
    # but frames don't have MOVE_TO_DISCARD with correct value
    if "手札を" in text and "控え室に置く" in text:
        # Extract number
        import re
        match = re.search(r'手札を(\d+)枚控え室に置く', text)
        if match:
            expected_value = int(match.group(1))
            has_correct_discard = False
            for frame in frames:
                if frame.get('op') == 'MOVE_TO_DISCARD':
                    if frame.get('value') == expected_value and frame.get('slot', {}).get('target_slot') == 'HAND':
                        has_correct_discard = True
                        break
            if not has_correct_discard:
                issues.append((i, f"Text says discard {expected_value} cards from hand but frames don't match"))
    
    # Check if text mentions "デッキの上からカードをX枚見る" (look at top X cards of deck)
    # but frames don't have LOOK_DECK with correct value
    if "デッキの上からカードを" in text and "見る" in text:
        import re
        match = re.search(r'デッキの上からカードを(\d+)枚見る', text)
        if match:
            expected_value = int(match.group(1))
            has_correct_look = False
            for frame in frames:
                if frame.get('op') == 'LOOK_DECK':
                    if frame.get('value') == expected_value:
                        has_correct_look = True
                        break
            if not has_correct_look:
                issues.append((i, f"Text says look at {expected_value} cards from deck but frames don't match"))
    
    # Check if text mentions "X枚を手札に加える" (add X cards to hand)
    # but frames don't have ADD_TO_HAND with correct value
    if "枚を手札に加え" in text or "枚を手札に加える" in text:
        import re
        match = re.search(r'(\d+)枚を手札に加え', text)
        if match:
            expected_value = int(match.group(1))
            has_correct_add = False
            for frame in frames:
                if frame.get('op') == 'ADD_TO_HAND':
                    if frame.get('value') == expected_value:
                        has_correct_add = True
                        break
            if not has_correct_add:
                issues.append((i, f"Text says add {expected_value} cards to hand but frames don't match"))

print(f"Reviewing abilities {start} to {end}")
print(f"Found {len(issues)} semantic issues:\n")

for ability_id, reason in issues:
    semantic_ability = semantic_map[ability_id]
    print(f"Ability {ability_id}: {reason}")
    print(f"  Text: {semantic_ability['primary_text_jp'][:80]}...")
    print()
