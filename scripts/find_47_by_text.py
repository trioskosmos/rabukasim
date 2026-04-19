#!/usr/bin/env python3
"""Find card 47 by ability text"""
import json

with open('data/ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('abilities', [])
for i, ability in enumerate(abilities):
    full_text = ability.get('full_text', '')
    if 'heart06' in full_text and 'heart01' in full_text:
        print(f"Index {i}")
        print(f"Cards: {ability.get('cards', [])}")
        print(f"Full text: {full_text[:200]}")
        print()
