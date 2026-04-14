import json

data = json.load(open('data/abilities_extracted_simple.json', 'r', encoding='utf-8'))

# Get abilities below 70% coverage
below_70 = [a for a in data['abilities'] if a['coverage'] < 0.7]
below_70.sort(key=lambda x: x['coverage'])

print(f"Abilities with < 70% coverage ({len(below_70)} total):")
print("=" * 80)
for i, ability in enumerate(below_70, 1):
    print(f"\n{i}. Coverage: {ability['coverage']:.1%}")
    print(f"   Ability: {ability['jp']}")
