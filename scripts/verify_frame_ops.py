#!/usr/bin/env python3
"""
Verify that all frame operations used in ability_frame_source.json are supported by the engine
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    frame_data = json.load(f)

# Frame operations supported by the engine (from generated_constants.rs)
SUPPORTED_OPS = {
    'NOP', 'RETURN', 'JUMP', 'JUMP_IF_FALSE',
    'DRAW', 'ADD_BLADES', 'ADD_HEARTS', 'REDUCE_COST', 'LOOK_DECK',
    'RECOVER_LIVE', 'BOOST_SCORE', 'RECOVER_MEMBER', 'BUFF_POWER', 'IMMUNITY',
    'MOVE_MEMBER', 'SWAP_CARDS', 'SEARCH_DECK', 'ENERGY_CHARGE',
    'SET_BLADES', 'SET_HEARTS', 'FORMATION_CHANGE', 'NEGATE_EFFECT',
    'ORDER_DECK', 'META_RULE', 'SELECT_MODE', 'MOVE_TO_DECK',
    'TAP_OPPONENT', 'PLACE_UNDER', 'FLAVOR_ACTION', 'RESTRICTION',
    'BATON_TOUCH_MOD', 'SET_SCORE', 'SWAP_ZONE', 'TRANSFORM_COLOR',
    'REVEAL_CARDS', 'LOOK_AND_CHOOSE', 'CHEER_REVEAL', 'ACTIVATE_MEMBER',
    'ADD_TO_HAND', 'COLOR_SELECT', 'TRIGGER_REMOTE', 'REDUCE_HEART_REQ',
    'MODIFY_SCORE_RULE', 'ADD_STAGE_ENERGY', 'SET_TAPPED', 'TAP_MEMBER',
    'PLAY_MEMBER_FROM_HAND', 'MOVE_TO_DISCARD', 'GRANT_ABILITY',
    'INCREASE_HEART_COST', 'REDUCE_YELL_COUNT', 'PLAY_MEMBER_FROM_DISCARD',
    'PAY_ENERGY', 'SELECT_MEMBER', 'DRAW_UNTIL', 'SELECT_PLAYER',
    'SELECT_LIVE', 'REVEAL_UNTIL', 'INCREASE_COST', 'PREVENT_PLAY_TO_SLOT',
    'SWAP_AREA', 'TRANSFORM_HEART', 'SELECT_CARDS', 'OPPONENT_CHOOSE',
    'PLAY_LIVE_FROM_DISCARD', 'REDUCE_LIVE_SET_LIMIT', 'SET_TARGET_SELF',
    'SET_TARGET_OPPONENT', 'PREVENT_SET_TO_SUCCESS_PILE', 'ACTIVATE_ENERGY',
    'PREVENT_ACTIVATE', 'SET_HEART_COST', 'PREVENT_BATON_TOUCH',
    'LOOK_DECK_DYNAMIC', 'REDUCE_SCORE', 'REPEAT_ABILITY',
    'LOSE_EXCESS_HEARTS', 'SKIP_ACTIVATE_PHASE', 'PAY_ENERGY_DYNAMIC',
    'PLACE_ENERGY_UNDER_MEMBER', 'CALC_SUM_COST', 'LOOK_REORDER_DISCARD',
    'DIV_VALUE', 'TRANSFORM_BLADES'
}

# Also support condition opcodes (these are in the range 200-255 and 301-399)
CONDITION_OPS = {
    'TURN_1', 'HAS_MEMBER', 'HAS_COLOR', 'COUNT_STAGE', 'COUNT_HAND',
    'COUNT_DISCARD', 'IS_CENTER', 'LIFE_LEAD', 'COUNT_GROUP',
    'GROUP_FILTER', 'OPPONENT_HAS', 'SELF_IS_GROUP', 'MODAL_ANSWER',
    'COUNT_ENERGY', 'HAS_LIVE_CARD', 'COST_CHECK', 'RARITY_CHECK',
    'HAND_HAS_NO_LIVE', 'COUNT_SUCCESS_LIVE', 'OPPONENT_HAND_DIFF',
    'SCORE_COMPARE', 'HAS_CHOICE', 'OPPONENT_CHOICE', 'COUNT_HEARTS',
    'COUNT_BLADES', 'OPPONENT_ENERGY_DIFF', 'HAS_KEYWORD',
    'DECK_REFRESHED', 'HAS_MOVED', 'HAND_INCREASED', 'COUNT_LIVE_ZONE',
    'COUNT_UNIQUE_COLORS', 'BATON', 'TYPE_CHECK', 'IS_IN_DISCARD',
    'AREA_CHECK', 'COST_LEAD', 'SCORE_LEAD', 'HEART_LEAD',
    'HAS_EXCESS_HEART', 'NOT_HAS_EXCESS_HEART', 'TOTAL_BLADES',
    'COST_COMPARE', 'BLADE_COMPARE', 'HEART_COMPARE', 'OPPONENT_HAS_WAIT',
    'IS_TAPPED', 'IS_ACTIVE', 'LIVE_PERFORMED', 'IS_PLAYER',
    'IS_OPPONENT', 'COUNT_ENERGY_EXACT', 'COUNT_BLADE_HEART_TYPES',
    'OPPONENT_HAS_EXCESS_HEART', 'SCORE_TOTAL_CHECK', 'MAIN_PHASE',
    'SELECT_MEMBER', 'SUCCESS_PILE_COUNT', 'IS_SELF_MOVE',
    'DISCARDED_CARDS', 'YELL_REVEALED_UNIQUE_COLORS', 'SYNC_COST',
    'SUM_VALUE', 'IS_WAIT', 'ON_ABILITY_RESOLVE',
    'TARGET_MEMBER_HAS_NO_HEARTS', 'COUNT_LIVE_HEARTS',
    'COUNT_SUCCESS_LIVE_SCORE'
}

# Custom frame operations I may have used that need to be checked
CUSTOM_OPS = set()

# Collect all frame operations used
all_used_ops = set()
unsupported_ops = set()

for ability in frame_data['abilities']:
    if 'frames' in ability:
        for frame in ability['frames']:
            op = frame.get('op', '')
            all_used_ops.add(op)
            if op not in SUPPORTED_OPS and op not in CONDITION_OPS:
                unsupported_ops.add(op)

print(f"Total frame operations used: {len(all_used_ops)}")
print(f"Unsupported frame operations: {len(unsupported_ops)}")

if unsupported_ops:
    print("\nUnsupported frame operations:")
    for op in sorted(unsupported_ops):
        print(f"  - {op}")
        # Find which abilities use this op
        abilities_using_op = []
        for i, ability in enumerate(frame_data['abilities']):
            if 'frames' in ability:
                for frame in ability['frames']:
                    if frame.get('op') == op:
                        abilities_using_op.append(i)
                        break
        print(f"    Used in abilities: {abilities_using_op[:10]}{'...' if len(abilities_using_op) > 10 else ''}")
else:
    print("\nAll frame operations are supported by the engine!")
