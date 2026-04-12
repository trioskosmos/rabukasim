#!/usr/bin/env python3
"""
Find ability by card reference
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

# Search for card refs PL!-bp3-007-P and PL!-bp3-007-R
for i, ability in enumerate(frame_data['abilities']):
    if 'card_refs' in ability:
        for card_ref in ability['card_refs']:
            if 'PL!-bp3-007' in card_ref.get('card_no', ''):
                print(f"Found ability {i} with card_ref {card_ref['card_no']}")
                print(f"Text: {ability.get('primary_text_jp', '')}")
                print(f"\nFrames:")
                for frame in ability.get('frames', []):
                    print(f"  Frame {frame['frame_index']}: {frame['op']}")
                    if 'value' in frame:
                        print(f"    value: {frame['value']}")
                    if 'attr' in frame:
                        print(f"    attr: {frame['attr']}")
                print(f"\nFrame verification:")
                if 'frame_verification' in ability:
                    print(json.dumps(ability['frame_verification'], indent=2, ensure_ascii=False))
                else:
                    print("  No frame_verification field")
                break
