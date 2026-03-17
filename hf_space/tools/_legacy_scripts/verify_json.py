import json
import os

path = "data/cards_compiled.json"
if not os.path.exists(path):
    print(f"File not found: {path}")
else:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        card = data.get("PL!SP-sd1-009-SD")
        if card:
            print(f"Card found: {card.get('name')}")
            abilities = card.get("abilities", [])
            for i, ab in enumerate(abilities):
                print(f"Ability {i}: Trigger {ab.get('trigger')}")
                print(f"  Text: {ab.get('raw_text')}")
        else:
            print("Card PL!SP-sd1-009-SD not found")
