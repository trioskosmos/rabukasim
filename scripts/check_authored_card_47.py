#!/usr/bin/env python3
"""Check if card 47 exists in authored frame source"""
import json

with open('data/ability_frame_source_authored.json', encoding='utf-8') as f:
    authored = json.load(f)

abilities = authored.get('abilities', [])
print(f"Total abilities in authored frame source: {len(abilities)}")

for i, ability in enumerate(abilities):
    source_texts = ability.get('source_ability_texts', [])
    for st in source_texts:
        card_examples = st.get('card_examples', [])
        for card_ref in card_examples:
            if 'PL!-bp3-024-L' in card_ref or '47' in card_ref:
                print(f"Found card 47 at index {i}")
                print(json.dumps(ability, ensure_ascii=False, indent=2))
