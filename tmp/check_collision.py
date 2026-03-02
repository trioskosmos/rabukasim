import json
db = json.load(open('data/cards_compiled.json', encoding='utf-8'))
for cid in ['334', '4430']:
    if cid in db['member_db']:
        c = db['member_db'][cid]
        print(f"ID {cid}: {c['name']} groups={c['groups']}")
    else:
        print(f"ID {cid} not found")
