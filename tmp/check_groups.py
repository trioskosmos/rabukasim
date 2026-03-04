import json
with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

output = []
for db_name in ['member_db', 'live_db']:
    for cid, card in db.get(db_name, {}).items():
        if cid in ['459', '234', '100', '1179']:
            msg = f"DB: {db_name}, ID: {cid}, No: {card.get('card_no')}, Groups: {card.get('groups')}"
            print(msg)
            output.append(msg)

with open('reports/group_check_utf8.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
