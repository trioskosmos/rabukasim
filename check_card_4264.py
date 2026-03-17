import json

data = json.load(open('data/cards_compiled.json', encoding='utf-8'))
card = data.get('member_db', {}).get('4264')

if not card:
    print("Card 4264 not found")
else:
    print(f"Card: {card.get('name')} ({card.get('card_id')})")
    print(f"Total abilities: {len(card.get('abilities', []))}")
    
    for i, ability in enumerate(card.get('abilities', [])):
        print(f"\n=== Ability {i} ===")
        print(f"Raw text: {ability.get('raw_text', 'N/A')[:150]}")
        print(f"Trigger: {ability.get('trigger')}")
        print(f"Conditions: {ability.get('conditions')}")
        if ability.get('filters'):
            print(f"Filters: {ability['filters'][0]}")
