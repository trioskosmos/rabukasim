import json

with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

card_47 = data['member_db']['47']
print(json.dumps(card_47, indent=2, ensure_ascii=False))
