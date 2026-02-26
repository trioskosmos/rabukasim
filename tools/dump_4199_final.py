import json

with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

for c in cards:
    if str(c.get('card_id', '')) == '4199':
        print(f"FOUND ID 4199: {c.get('card_number')}")
        print(json.dumps(c.get('abilities', []), indent=2, ensure_ascii=False))
