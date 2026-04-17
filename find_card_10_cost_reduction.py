"""Find card 10 cost reduction ability in abilities_extracted_from_cards.json."""

import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

abilities = data['unique_abilities']

# Find abilities with cost reduction patterns that mention hand cards
cost_reduction_abilities = []
for ability in abilities:
    full_text = ability.get('full_text', '')
    costless_text = ability.get('costless_text', '')
    effect = ability.get('effect', {})
    
    # Look for cost reduction with hand cards
    if 'コスト' in full_text and ('手札' in full_text or '手元' in full_text):
        cost_reduction_abilities.append(ability)
    elif '安く' in full_text or '減らす' in full_text:
        cost_reduction_abilities.append(ability)

print(f"Found {len(cost_reduction_abilities)} abilities with cost reduction")
for i, ability in enumerate(cost_reduction_abilities[:10]):
    print(f"\nAbility {i+1}:")
    print(f"Full text: {ability.get('full_text')[:200]}...")
    print(f"Cost: {ability.get('cost')}")
    print(f"Effect: {ability.get('effect')}")
