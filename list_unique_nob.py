
import json
import os

data_path = r'data\cards_compiled.json'
with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

db = data.get('member_db', {})
remainder_nos = set()
discard_trigger_nos = set()

for k, v in db.items():
    if not isinstance(v, dict): continue
    card_no = v.get('card_no', 'Unknown')
    for ab in v.get('abilities', []):
        p = ab.get('pseudocode', '')
        if 'REMAINDER' in p:
            remainder_nos.add(card_no)
        if 'ACTIVATED (In Discard)' in p:
            discard_trigger_nos.add(card_no)

print("REMAINDER:", sorted(list(remainder_nos))[:20])
print("DISCARD_TRIGGER:", sorted(list(discard_trigger_nos))[:20])
