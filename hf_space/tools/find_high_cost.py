import json

with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for cid, card in data.get("member_db", {}).items():
    if card.get("cost", 0) >= 11:
        print(f"Member ID {cid}: {card.get('card_no')} (Cost {card.get('cost')})")

for cid, card in data.get("live_db", {}).items():
    if card.get("cost", 0) >= 11:
        print(f"Live ID {cid}: {card.get('card_no')} (Cost {card.get('cost')})")
