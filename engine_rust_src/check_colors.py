
import json
with open('../data/cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    def find_in_db(db_name, target_id):
        return data.get(db_name, {}).get(str(target_id))

    for cid in [101, 102, 103, 104, 105]:
        card = find_in_db('member_db', cid)
        if card:
            print(f"ID {cid:3} | Name: {ascii(card['name']):20} | Hearts: {card['hearts']}")

    card = find_in_db('live_db', 519)
    if card:
        print(f"ID 519 | Name: {ascii(card['name']):20} | Req: {card['required_hearts']}")
