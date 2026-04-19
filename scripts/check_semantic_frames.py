import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    extracted = json.load(f)

# Find card 47
card_47 = None
for card_id, card_data in extracted.items():
    if card_id == '47':
        card_47 = card_data
        break

if card_47:
    print(f"Card 47: {card_47.get('name', 'Unknown')}")
    print(f"\nAbilities:")
    for idx, ability in enumerate(card_47.get('abilities', [])):
        print(f"\nAbility {idx}:")
        print(f"  Trigger: {ability.get('trigger', 'Unknown')}")
        print(f"  Text: {ability.get('text', '')[:100]}...")
        print(f"  Effects: {ability.get('effects', [])}")
        print(f"  Conditions: {ability.get('conditions', [])}")
