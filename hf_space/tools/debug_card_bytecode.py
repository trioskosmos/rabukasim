#!/usr/bin/env python3
"""Debug script to examine compiled card bytecode for optional cost handling."""

import json

def inspect_card_from_obj(card):
    card_no = card.get('card_no', 'UNKNOWN')
    print(f"==================== {card_no} ====================")
    print(f"Number of abilities: {len(card.get('abilities', []))}")
    
    for i, ability in enumerate(card.get('abilities', [])):
        print(f"\n=== Ability {i} ===")
        print(f"Trigger: {ability.get('trigger')}")
        costs = ability.get('costs', [])
        print(f"Costs: {len(costs)}")
        for j, cost in enumerate(costs):
            print(f"  Cost {j}:")
            print(f"    type: {cost.get('type')}")
            print(f"    value: {cost.get('value')}")
            print(f"    is_optional: {cost.get('is_optional')}")
            print(f"    runtime_opcode: {cost.get('runtime_opcode')}")
            print(f"    runtime_attr: {cost.get('runtime_attr')} (0x{cost.get('runtime_attr', 0):016x})")
            print(f"    runtime_slot: {cost.get('runtime_slot')}")
        
        bytecode = ability.get('bytecode', [])
        print(f"Bytecode (first 20 ints): {bytecode[:20]}")
        print(f"Pseudocode:\n{ability.get('pseudocode', 'N/A')}")

def inspect_card(card_no):
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    # Find card in the database structure
    card = None
    full_db = {}
    full_db.update(db.get('member_db', {}) or {})
    full_db.update(db.get('live_db', {}) or {})
    full_db.update(db.get('energy_db', {}) or {})
    
    card = full_db.get(card_no) or full_db.get(card_no.replace('+', '＋'))
    if not card:
        print(f"Card {card_no} not found in database")
        # List similar cards  
        similar = [k for k in full_db.keys() if 'bp1-001' in k or 'bp2-001' in k]
        if similar:
            print(f"Similar cards: {similar}")
        return

if __name__ == '__main__':
    print("=== EXAMINING DATABASE STRUCTURE ===\n")
    
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    member_db = db.get('member_db', {})
    print(f'member_db type: {type(member_db).__name__}')
    
    if isinstance(member_db, dict):
        print(f'member_db has {len(member_db)} keys')
        ll_keys = [k for k in member_db.keys() if k.startswith('LL-')][:5]
        print(f'Found {len(ll_keys)} LL cards')
        if ll_keys:
            for key in ll_keys[:3]:
                card = member_db[key]
                print(f"  {key}: has {len(card.get('abilities', []))} abilities")
    
    print("\n\n=== EXAMINING OPTIONAL COST COMPILATION ===\n")
    print("Looking for LL-bp2-001-R+ and LL-bp1-001-R+...")
    
    # Try both with + and ＋
    for card_no in ['LL-bp2-001-R+', 'LL-bp2-001-R＋', 'LL-bp1-001-R+', 'LL-bp1-001-R＋']:
        if card_no in member_db:
            print(f"\nFound {card_no}!")
            inspect_card_from_obj(member_db[card_no])
            break
