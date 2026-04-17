import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

abilities = data['unique_abilities']

# Find abilities with card 10
card_10_abilities = []
for ability in abilities:
    cards = ability.get('cards', [])
    for card in cards:
        if '10' in card and 'PL!' in card:
            card_10_abilities.append(ability)
            break

print(f"Found {len(card_10_abilities)} abilities with card 10")
for i, ability in enumerate(card_10_abilities):
    print(f"\nAbility {i+1}:")
    print(f"Full text: {ability.get('full_text')}")
    print(f"Cost: {ability.get('cost')}")
    print(f"Effect: {ability.get('effect')}")
