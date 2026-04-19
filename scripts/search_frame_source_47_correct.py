#!/usr/bin/env python3
"""Search frame source for card 47 using correct structure"""
import json

with open('data/ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('abilities', [])
print(f"Total abilities in frame source: {len(abilities)}")

for i, ability in enumerate(abilities):
    source_texts = ability.get('source_ability_texts', [])
    for st in source_texts:
        card_examples = st.get('card_examples', [])
        for card_ref in card_examples:
            if 'PL!-bp3-024-L' in card_ref or '47' in card_ref:
                print(f"Found at index {i}")
                print(f"Card examples: {card_examples}")
                frames = ability.get('frames', [])
                print(f"Number of frames: {len(frames)}")
                for j, frame in enumerate(frames[:20]):
                    print(f"  Frame {j}: {frame.get('op')}")
                    if frame.get('op') == 'SELECT_MEMBER':
                        print(f"    Attr: {frame.get('attr')}")
                print()
