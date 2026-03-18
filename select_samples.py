
import json
import os

data_path = r'data\cards_compiled.json'
if not os.path.exists(data_path):
    print("Data path not found")
    exit(1)

with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

db = data.get('member_db', {})
remainder_cards = []
discard_trigger_cards = []

for k, v in db.items():
    if not isinstance(v, dict): continue
    card_no = v.get('card_no', 'Unknown')
    for ab in v.get('abilities', []):
        p = ab.get('pseudocode', '')
        if 'REMAINDER' in p and len(remainder_cards) < 5:
            remainder_cards.append((k, card_no))
        if 'ACTIVATED (In Discard)' in p and len(discard_trigger_cards) < 5:
            discard_trigger_cards.append((k, card_no))

print("--- REMAINDER CARDS ---")
for k, no in remainder_cards:
    print(f"ID: {k} | No: {no}")

print("\n--- DISCARD TRIGGER CARDS ---")
for k, no in discard_trigger_cards:
    print(f"ID: {k} | No: {no}")
