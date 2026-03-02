import json
db = json.load(open('data/cards_compiled.json', encoding='utf-8'))
for cid_str, card in db['member_db'].items():
    cid = int(cid_str)
    if cid % 4096 == 334:
        print(f"ID {cid}: {card['name']} groups={card['groups']} no={card['card_no']}")
