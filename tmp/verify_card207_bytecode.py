import json

path = 'data/cards_compiled.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

card_id = '207'
card = data['live_db'][card_id]

print(f"--- Verification for Card {card_id} ---")
print(f"Card Name: {card.get('name')}")
print(f"Units (should be 13, 14, 15): {card.get('units')}")

for i, ab in enumerate(card.get('abilities', [])):
    semantic = ab.get('semantic_form', {})
    print(f"\nAbility {i}:")
    print(f"  Trigger: {semantic.get('trigger')}")
    
    # Check effects for BOOST_SCORE or similar
    for eff in ab.get('effects', []):
        if eff.get('effect_type') == 16: # O_BOOST_SCORE
            attr = eff.get('params', {}).get('A')
            if attr:
                group_enabled = (attr >> 4) & 1
                group_id = (attr >> 5) & 0x7F
                unit_enabled = (attr >> 16) & 1
                unit_id = (attr >> 17) & 0x7F
                print(f"  BOOST_SCORE detected:")
                print(f"    Attribute: {attr}")
                print(f"    Group mapping: enabled={group_enabled}, id={group_id}")
                print(f"    Unit mapping: enabled={unit_enabled}, id={unit_id}")
                
    # Also check conditions if any
    for cond in ab.get('conditions', []):
        attr = cond.get('params', {}).get('A')
        if attr:
            group_enabled = (attr >> 4) & 1
            group_id = (attr >> 5) & 0x7F
            print(f"  Condition detected (A={attr}): group_enabled={group_enabled}, group_id={group_id}")

print("\n--- End of Verification ---")
