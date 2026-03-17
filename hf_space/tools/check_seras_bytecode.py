import json

with open('data/cards_compiled.json', encoding='utf-8') as f:
    db = json.load(f)

member_db = db.get('member_db', {})

# Find Seras
for card_id, card_data in member_db.items():
    if isinstance(card_data, dict) and card_data.get('card_no') == 'PL!HS-bp5-007-R':
        print(f"Found Seras with ID {card_id}!")
        abilities = card_data.get('abilities', [])
        print(f"Seras has {len(abilities)} abilities\n")
        
        for i, ability in enumerate(abilities):
            print(f"=== Ability {i} ===")
            if isinstance(ability, dict):
                print(f"Keys: {list(ability.keys())}")
                # Check for bytecode
                if 'bytecode' in ability:
                    bc = ability['bytecode']
                    print(f"Bytecode length: {len(bc) if isinstance(bc, (list, str)) else 'not list/str'}")
                    if isinstance(bc, list):
                        print(f"Bytecode (first 50): {bc[:50]}")
                        if 15 in bc:  # RECOVER_LIVE
                            print(f"  *** CONTAINS RECOVER_LIVE (15) ***")
                        if 58 in bc:  # MOVE_TO_DISCARD
                            print(f"  *** CONTAINS MOVE_TO_DISCARD (58) ***")
            print()
        break
else:
    print("Seras not found!")
