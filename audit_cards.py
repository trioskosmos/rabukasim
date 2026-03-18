
import json
import os

data_path = r'data\cards_compiled.json'
results = []

if os.path.exists(data_path):
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check in member_db
    member_db = data.get('member_db', {})
    for card_id, v in member_db.items():
        if not isinstance(v, dict):
            continue
        card_no = v.get('card_no', 'Unknown')
        for ab in v.get('abilities', []):
            p = ab.get('pseudocode', '')
            if 'REMAINDER' in p or 'ACTIVATED (In Discard)' in p:
                results.append({
                    "card_id": card_id,
                    "card_no": card_no,
                    "pseudocode": p
                })

for res in results:
    type_found = []
    if 'REMAINDER' in res['pseudocode']: type_found.append('REMAINDER')
    if 'ACTIVATED (In Discard)' in res['pseudocode']: type_found.append('DISCARD_TRIGGER')
    
    print(f"ID: {res['card_id']} | No: {res['card_no']} | Patterns: {', '.join(type_found)}")
    print(f"Pseudocode: {res['pseudocode']}")
    print("-" * 20)
print(f"Total cards found: {len(results)}")
