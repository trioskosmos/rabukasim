import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

abilities = data['unique_abilities']

# Find abilities with cost reduction patterns
cost_reduction_abilities = []
for ability in abilities:
    full_text = ability.get('full_text', '')
    if 'コスト' in full_text and ('減らす' in full_text or '減少' in full_text or '安く' in full_text):
        cost_reduction_abilities.append(ability)

print(f"Found {len(cost_reduction_abilities)} abilities with cost reduction")
for i, ability in enumerate(cost_reduction_abilities[:10]):
    print(f"\nAbility {i+1}:")
    print(f"Full text: {ability.get('full_text')}")
    print(f"Cost: {ability.get('cost')}")
    print(f"Effect: {ability.get('effect')}")
