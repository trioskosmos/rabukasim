import json

with open('../data/cards_compiled.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Check card 590 (Mei)
member = d.get('member_db', {}).get('590')
if member:
    print(f"Card 590 (Mei): {member.get('card_no')}")
    print(f"  Abilities: {len(member.get('abilities', []))}")
    for i, ab in enumerate(member.get('abilities', [])):
        print(f"\n  Ability {i}:")
        print(f"    trigger: {ab.get('trigger')}")
        print(f"    bytecode: {ab.get('bytecode')}")
        print(f"    effects: {len(ab.get('effects', []))}")
        for j, ef in enumerate(ab.get('effects', [])):
            print(f"      Effect {j}: type={ef.get('effect_type')}, value={ef.get('value')}, target={ef.get('target')}")
        print(f"    conditions: {ab.get('conditions', [])}")
        print(f"    costs: {ab.get('costs', [])}")
        print(f"    is_once_per_turn: {ab.get('is_once_per_turn')}")
