import json
with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    d = json.load(f)
mdb = d.get('member_db', {})
k = next(iter(mdb))
ab = mdb[k]['abilities'][0]
print(f"Keys: {list(ab.keys())}")
print(f"Pseudocode: {repr(ab.get('pseudocode'))}")
