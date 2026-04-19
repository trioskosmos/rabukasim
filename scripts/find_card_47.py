import json

with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Search for card 47 in member_db
for card_id, card_data in data['member_db'].items():
    if card_data.get('card_no') == 'PL!-bp3-024-L':
        print(f"Found card 47 with ID: {card_id}")
        print(json.dumps(card_data, indent=2, ensure_ascii=False))
        break
