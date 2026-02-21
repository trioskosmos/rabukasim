import json
import os

cards_file = 'data/cards_compiled.json'
if not os.path.exists(cards_file):
    print(f"Error: {cards_file} not found")
    exit(1)

with open(cards_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

member_db = data.get('member_db', {})
live_db = data.get('live_db', {})

card_map = {}
for cid, card in member_db.items():
    card_map[card['card_no']] = card['card_id']
for cid, card in live_db.items():
    card_map[card['card_no']] = card['card_id']

archetypes = [
    'PL!-bp3-012-PR', 'PL!N-bp1-002-R＋', 'PL!N-bp1-003-R＋', 
    'PL!N-bp1-006-R＋', 'PL!N-bp1-012-R＋', 'PL!SP-bp1-002-R＋', 
    'PL!N-bp1-007-R', 'PL!S-bp2-024-L', 'PL!SP-bp1-003-R＋', 
    'PL!HS-PR-010-PR'
]

print("--- Mapping Archetypes ---")
for no in archetypes:
    print(f"{no}: {card_map.get(no, 'MISSING')}")

# Also check for "archetype_01" if it exists in data
arch01 = 'PL!-sd1-005-SD'
print(f"{arch01}: {card_map.get(arch01, 'MISSING')}")
