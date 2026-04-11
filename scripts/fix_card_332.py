#!/usr/bin/env python3
"""
Fix script for card 332 (test_q196_select_member_empty)
Remove SUM_VALUE check and add JUMP_IF_FALSE to make blade granting optional
"""

import json

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Load the data
filepath = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\ability_frame_source.json'
data = load_json(filepath)

# Find card 332 and fix its frames
for ability in data['abilities']:
    for card_ref in ability.get('card_refs', []):
        if card_ref.get('card_id') == 332:
            print(f"Found card 332 in ability with trigger: {ability.get('trigger')}")
            # Fix the frames - remove SUM_VALUE, add JUMP_IF_FALSE
            new_frames = [
                {
                    'op': 'PAY_ENERGY',
                    'frame_index': 0,
                    'value': 1,
                    'slot': {'target_slot': 'CONTEXT'}
                },
                {
                    'op': 'DRAW',
                    'frame_index': 1,
                    'value': 1,
                    'slot': {'target_slot': 'CONTEXT'}
                },
                {
                    'op': 'SELECT_MEMBER',
                    'frame_index': 2,
                    'value': 1,
                    'attr': {
                        'target_player': 'SELF',
                        'group_enabled': 1,
                        'group_id': 'NIJIGASAKI'
                    },
                    'slot': {
                        'target_slot': 'CONTEXT',
                        'source_zone': 'STAGE'
                    }
                },
                {
                    'op': 'JUMP_IF_FALSE',
                    'frame_index': 3,
                    'value': 5
                },
                {
                    'op': 'ADD_BLADES',
                    'frame_index': 4,
                    'value': 1,
                    'slot': {'target_slot': 'CONTEXT'}
                },
                {
                    'op': 'RETURN',
                    'frame_index': 5
                }
            ]
            ability['frames'] = new_frames
            ability['frame_verification'] = {
                'verified': True,
                'notes': [
                    'Trigger: ACTIVATED',
                    'Text: {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このカードを手札から控え室に置く：カードを1枚引き、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は{{icon_blade.png|ブレード}}を得る。この能力は、このカードが手札にある場合のみ起動できる。',
                    'Fixed: Removed SUM_VALUE check at frame 0, added JUMP_IF_FALSE after SELECT_MEMBER to make blade granting optional when no member is selected',
                    'Frame 0: PAY_ENERGY - pays 1 energy',
                    'Frame 1: DRAW - draws 1 card',
                    'Frame 2: SELECT_MEMBER - selects 1 Nijigasaki member from stage (optional)',
                    'Frame 3: JUMP_IF_FALSE - jumps to RETURN if no member selected',
                    'Frame 4: ADD_BLADES - gives blade to selected member',
                    'Frame 5: RETURN'
                ],
                'text_mapping': {
                    'このカードを手札から控え室に置く': 'Implicit in PAY_ENERGY',
                    'カードを1枚引き': 'Frame 1: DRAW',
                    'ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は{{icon_blade.png|ブレード}}を得る': 'Frame 2-4: SELECT_MEMBER + JUMP_IF_FALSE + ADD_BLADES (conditional)'
                }
            }
            print(f'Fixed frames for card 332')
            break

# Save the data
save_json(filepath, data)
print('File updated successfully')
