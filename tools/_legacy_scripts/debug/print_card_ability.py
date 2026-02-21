import json

with open("engine/data/cards.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    for k, v in data.items():
        if v.get("card_no") == "PL!S-bp2-007-P":
            print(f"Card: {v.get('card_no')}")
            print(f"Ability: {v.get('ability')}")
            break
