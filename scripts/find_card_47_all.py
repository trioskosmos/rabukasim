import json

with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Search for card 47 in all databases
for db_name, db_data in data.items():
    if isinstance(db_data, dict):
        for card_id, card_data in db_data.items():
            if isinstance(card_data, dict) and card_data.get('card_no') == 'PL!-bp3-024-L':
                print(f"Found card 47 in {db_name} with ID: {card_id}")
                print(json.dumps(card_data, indent=2, ensure_ascii=False))
                break
