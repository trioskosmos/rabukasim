import json

with open("engine/data/cards.json", "r", encoding="utf-8") as f:
    data = json.load(f)

card_code = "PL!S-PR-013-PR"
if card_code in data:
    c = data[card_code]
    print(f"Card: {c['name']} ({card_code})")
    print(f"Cost: {c.get('cost')}")
    print(f"Ability: {c.get('ability', c.get('text'))}")
else:
    print(f"Card {card_code} not found.")
