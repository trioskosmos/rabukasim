"""Check effect data structure."""
import json

with open('data/abilities_extracted_from_cards.json', encoding='utf-8') as f:
    data = json.load(f)

for i, ability in enumerate(data['unique_abilities'][:10]):
    effect = ability.get('effect', {})
    print(f"Ability {i}:")
    print(f"  Effect type: {type(effect)}")
    print(f"  Effect keys: {list(effect.keys()) if isinstance(effect, dict) else 'N/A'}")
    print(f"  Effect value: {effect}")
    print()
