#!/usr/bin/env python3
import json

with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Show first few abilities
for i, ability in enumerate(data['abilities'][:3]):
    text = ability['source_ability_texts'][0]
    trigger = ability['trigger']
    print(f'=== Ability {i+1} ===')
    print(f'Trigger: {trigger}')
    print(f'JP: {text["jp"][:80]}...')
    print(f'Logic: {text["logic"][:100]}...')
    print(f'Cards: {len(text["cards"])} cards')
    print()
