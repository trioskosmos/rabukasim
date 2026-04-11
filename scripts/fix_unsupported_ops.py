#!/usr/bin/env python3
"""
Fix unsupported frame operations by mapping them to engine-supported operations
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Mapping of unsupported ops to supported replacements
OP_REPLACEMENTS = {
    'CANNOT_ACTIVATE': 'PREVENT_ACTIVATE',
    'CANNOT_LIVE': 'PREVENT_SET_TO_SUCCESS_PILE',
    'CHECK_ALL_HEART_TYPES': 'COUNT_BLADE_HEART_TYPES',
    'CHECK_ALL_MEMBERS': 'HAS_MEMBER',  # Will need proper filter
    'COUNT_BLADE_HEART_CARDS': 'GROUP_FILTER',  # Will need proper filter
    'COUNT_CARDS': 'COUNT_HAND',  # Will need proper zone
    'COUNT_ENERGY_UNDER_MEMBER': None,  # Remove
    'COUNT_LIVE_CARDS': 'COUNT_LIVE_ZONE',
    'COUNT_MOVED_STAGE': 'HAS_MOVED',
    'COUNT_REVEALED_LIVE': 'COUNT_LIVE_ZONE',  # Will need revealed filter
    'COUNT_SUCCESS': 'COUNT_SUCCESS_LIVE',
    'COUNT_UNIQUE_NAMES': 'GROUP_FILTER',  # Will need unique filter
    'COUNT_YELL_SCORE': 'SUM_VALUE',
    'HAS_MOST_HEARTS': 'COUNT_HEARTS',
    'HAS_NOT_MOVED': 'HAS_MOVED',  # Will need negation
    'IDENTITY_CHANGE': None,  # Remove
    'INCREASE_HEART_REQ': 'INCREASE_HEART_COST',
    'IN_CENTER': 'IS_CENTER',
    'IN_SUCCESS_PILE': None,  # Remove
    'IS_SELF_TAP': 'IS_TAPPED',
    'JUMP_IF_EQUAL': 'JUMP_IF_FALSE',  # Will need negation
    'JUMP_IF_NOT_EQUAL': 'JUMP_IF_FALSE',
    'JUMP_IF_TRUE': 'JUMP_IF_FALSE',  # Will need negation
    'LOSE_BLADE_HEARTS': None,  # Remove
    'MOVE_ENERGY_UNDER_MEMBER': 'PLACE_ENERGY_UNDER_MEMBER',
    'MOVE_REVEALED_TO_DISCARD': 'MOVE_TO_DISCARD',
    'MOVE_TO_ENERGY_DECK': 'MOVE_TO_DECK',
    'MOVE_TO_HAND': 'ADD_TO_HAND',
    'OPPONENT_TAP_COST_LE4': 'TAP_OPPONENT',
    'PAY_ENERGY_OPTIONAL': 'PAY_ENERGY',
    'PHASE_CHECK': 'MAIN_PHASE',
    'REMOVE_HEARTS': 'LOSE_EXCESS_HEARTS',
    'REPEAT_YELL': None,  # Remove
    'SCORE_CHECK': 'SCORE_COMPARE',
    'SUM_COST': 'CALC_SUM_COST',
    'SUM_ENERGY': 'COUNT_ENERGY',
    # These need special handling
    'CHECK_SELF_MOVE_OR_ENERGY': None,  # Split into two checks
    'HAS_HIGHEST_COST_CENTER': None,  # Remove
    'IS_SELF_APPEAR_OR_MOVE': 'IS_SELF_MOVE',
}

# Abilities that need special handling
SPECIAL_HANDLING = {
    595: 'CHECK_SELF_MOVE_OR_ENERGY',  # Split into two separate conditions
    468: 'HAS_HIGHEST_COST_CENTER',  # Remove this frame
    610: 'OPPONENT_TAP_COST_LE4',  # Add proper filter to TAP_OPPONENT
}

fixed_count = 0
removed_count = 0
special_count = 0

for i, ability in enumerate(data['abilities']):
    if 'frames' not in ability:
        continue
    
    frames = ability['frames']
    new_frames = []
    
    for frame in frames:
        op = frame.get('op', '')
        
        if op in OP_REPLACEMENTS:
            replacement = OP_REPLACEMENTS[op]
            if replacement is None:
                # Remove this frame
                removed_count += 1
                print(f"Ability {i}: Removed unsupported op '{op}'")
                continue
            else:
                # Replace with supported op
                frame['op'] = replacement
                fixed_count += 1
                print(f"Ability {i}: Replaced '{op}' with '{replacement}'")
        elif i in SPECIAL_HANDLING:
            special_op = SPECIAL_HANDLING[i]
            if op == special_op:
                if special_op == 'HAS_HIGHEST_COST_CENTER':
                    # Remove this frame
                    removed_count += 1
                    print(f"Ability {i}: Removed special frame '{op}'")
                    continue
                elif special_op == 'OPPONENT_TAP_COST_LE4':
                    # Replace with TAP_OPPONENT and add cost filter
                    frame['op'] = 'TAP_OPPONENT'
                    if 'params' not in frame:
                        frame['params'] = {}
                    frame['params']['filter'] = 'COST_LE4'
                    fixed_count += 1
                    print(f"Ability {i}: Replaced '{op}' with 'TAP_OPPONENT' with cost filter")
                    continue
        
        new_frames.append(frame)
    
    # Re-index frames
    for idx, frame in enumerate(new_frames):
        frame['frame_index'] = idx
    
    ability['frames'] = new_frames

# Save the updated data
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nSummary:")
print(f"Fixed: {fixed_count} frame operations")
print(f"Removed: {removed_count} frame operations")
print(f"Total abilities modified: {fixed_count + removed_count}")
