import json

data = json.load(open('data/abilities_extracted_simple.json', 'r', encoding='utf-8'))

# Sort by coverage ascending
sorted_abilities = sorted(data['abilities'], key=lambda x: x['coverage'])

print("Top 20 abilities with lowest coverage:")
print("=" * 80)
for i, ability in enumerate(sorted_abilities[:20], 1):
    print(f"\n{i}. Coverage: {ability['coverage']:.1%}")
    print(f"   Ability: {ability['jp']}")
    print(f"   Card examples: {', '.join(ability.get('card_examples', []))}")
