import json

with open('data/cards_compiled.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

# Find Umi (PL!-bp3-004-R+) - internal ID 4122
member_db = data['member_db']
for card_id, card_data in member_db.items():
    card_id_int = int(card_id)
    if card_id_int == 4122:
        number = card_data.get('number', '')
        print(f'Card ID: {card_id}')
        print(f'Number: {number}')
        print(f'Name: {card_data.get("name")}')
        abilities = card_data.get('abilities', [])
        print(f'Abilities: {len(abilities)}')
        for idx, ability in enumerate(abilities):
            bc = ability.get('bytecode', [])
            print(f'\n  Ability {idx}: {ability.get("trigger")}')
            print(f'    Bytecode (dec): {bc}')
            if bc:
                print(f'    Bytecode (hex): {[hex(x) for x in bc[:20]]}')
        break
