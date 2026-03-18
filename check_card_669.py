import json

with open('data/cards_compiled.json', encoding='utf-8') as f:
    data = json.load(f)

card = data['member_db'].get('669') or data['member_db'].get(669)
print(f'Card 669: {card.get("name")} / {card.get("card_no")}')
print(f'\nAbilities count: {len(card.get("abilities", []))}')

for idx, ability in enumerate(card.get('abilities', [])):
    bytecode = ability.get('bytecode', [])
    num_instr = len(bytecode) // 5 if len(bytecode) > 0 else 0
    print(f'\n  Ability {idx}:')
    print(f'    Bytecode length: {len(bytecode)} bytes ({num_instr} instructions)')
    print(f'    First 50 bytes: {bytecode[:50]}')
