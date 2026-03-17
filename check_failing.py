
import json
import os

data_path = r'data\cards_compiled.json'
with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

db = data.get('member_db', {})
failing = []

for k, v in db.items():
    if not isinstance(v, dict): continue
    for ab in v.get('abilities', []):
        p = ab.get('pseudocode', '')
        bytecode = ab.get('bytecode', [])
        if 'REMAINDER' in p:
            for i in range(0, len(bytecode), 5):
                if bytecode[i] == 58: # MOVE_TO_DISCARD
                    slot = bytecode[i+3]
                    if (slot >> 16) & 0xFF == 0:
                        failing.append((k, v.get('card_no'), p))
                        break

print(f"Total Failing: {len(failing)}")
for k, no, p in failing[:10]:
    print(f"ID: {k} | No: {no} | Pseudocode: {p[:100]}...")
