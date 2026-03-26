import json

with open('../data/cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

card_nos = set()
for db_key in ['member_db', 'live_db']:
    if db_key in data:
        for card in data[db_key].values():
            if 'card_no' in card:
                card_nos.add(card['card_no'])

with open('valid_card_nos.txt', 'w', encoding='utf-8') as f:
    for no in sorted(card_nos):
        f.write(no + '\n')

print(f"Extracted {len(card_nos)} card numbers.")
