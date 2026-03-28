import sys
sys.path.insert(0, '.')

import json
from compiler.main import _populate_semantic_from_frames
from engine.models.ability import Ability

# Load the compiled data
data = json.load(open('data/cards_compiled.json', encoding='utf-8'))

# Get first card with abilities
card = list(data['member_db'].values())[0]
print(f"Card: {card['card_no']}")

# Get first ability
ab_data = card['abilities'][0]
print(f"Ability trigger: {ab_data.get('trigger')}")
print(f"Frame program instructions: {len(ab_data.get('frame_program', {}).get('instructions', []))}")

# Create an Ability object from the data
from compiler.main import _ability_from_dict
ability = _ability_from_dict(ab_data)

print(f"\nBefore population:")
print(f"  effects: {len(ability.effects)}")
print(f"  conditions: {len(ability.conditions)}")
print(f"  costs: {len(ability.costs)}")

# Call the population function
_populate_semantic_from_frames([ability], card['card_no'])

print(f"\nAfter population:")
print(f"  effects: {len(ability.effects)}")
print(f"  conditions: {len(ability.conditions)}")
print(f"  costs: {len(ability.costs)}")

if ability.effects:
    for i, eff in enumerate(ability.effects):
        print(f"  Effect {i}: {eff.effect_type.name}, value={eff.value}")
