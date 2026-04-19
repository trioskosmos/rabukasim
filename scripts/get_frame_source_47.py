#!/usr/bin/env python3
"""Get the full frame source entry for card 47"""
import json

with open('data/ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('abilities', [])
for i, ability in enumerate(abilities):
    source_texts = ability.get('source_ability_texts', [])
    for st in source_texts:
        card_examples = st.get('card_examples', [])
        for card_ref in card_examples:
            if 'PL!-bp3-024-L' in card_ref:
                print(f"Found at index {i}")
                print(json.dumps(ability, ensure_ascii=False, indent=2))
