import json

with open("engine/data/cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

target_card = None
for card in cards:
    if card.get("card_no") == "PL!-sd1-006-SD":
        target_card = card
        break

if target_card:
    print(json.dumps(target_card, indent=2, ensure_ascii=False))
else:
    print("Card not found")
