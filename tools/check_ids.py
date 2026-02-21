import json
with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

m = {v['card_no']: k for k, v in d['member_db'].items()}

targets = [
    "PL!HS-PR-010-PR",
    "PL!SP-bp1-003-R＋",
    "PL!-bp3-014-N",
    "PL!-sd1-001-SD",
    "LL-bp4-001-R＋"
]

for t in targets:
    print(f"{t}: {m.get(t)}")
