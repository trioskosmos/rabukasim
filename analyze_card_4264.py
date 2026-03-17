import json

# Load compiled data
data = json.load(open('data/cards_compiled.json', encoding='utf-8'))

# Sample cards with unit 13
unit_13_cards = []
for card_id, card in data.get('member_db', {}).items():
    if card.get('units') and 13 in card.get('units'):
        unit_13_cards.append((card_id, card.get('name')))
        
print(f"Unit 13 contains {len(unit_13_cards)} cards:")
for cid, name in sorted(unit_13_cards)[:15]:
    print(f"  {cid}: {name}")

# Now check what cards can be selected by card 4264's ability
print("\n\nCard 4264's activate ability filter:")
card_4264 = data['member_db']['4264']
ability_1 = card_4264['abilities'][1]
print(f"Raw text:\n{ability_1['raw_text']}")
print(f"\nFilter details:")
filt = ability_1['filters'][0]
print(f"  Unit ID: {filt['unit_id']} (enabled: {filt['unit_enabled']})")
print(f"  Group ID: {filt['group_id']} (enabled: {filt['group_enabled']})")
print(f"  Cost threshold: {filt['value_threshold']} (is_le: {filt['is_le']}, is_cost_type: {filt['is_cost_type']})")
print(f"  Zone mask: {filt['zone_mask']} (7=discard)")
print(f"  Summary: {filt['summary']}")

# Verify: Can only select cards that match ALL enabled filters
print(f"\n\nCards that CAN be selected by this ability:")
eligible = []
for card_id, card in data.get('member_db', {}).items():
    if 13 not in card.get('units', []):
        continue  # Not from unit 13
    if card.get('cost', 0) > 4:
        continue  # Cost too high
    eligible.append((card_id, card.get('name'), card.get('cost', 0)))

for cid, name, cost in sorted(eligible)[:15]:
    print(f"  {cid}: {name} (cost {cost})")
