import json

path = "engine/data/cards.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

card = data.get("LL-bp1-001-R＋")
if card:
    print(json.dumps(card, indent=2, ensure_ascii=False))
else:
    print("Card not found")
