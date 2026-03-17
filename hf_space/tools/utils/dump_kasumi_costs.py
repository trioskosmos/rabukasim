import json
import os

path = "engine/data/cards_compiled.json"
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    card = data["member_db"]["470"]
    print(f"CARD: {card['card_no']}")
    for i, ab in enumerate(card["abilities"]):
        print(f"AB {i}: trigger={ab.get('trigger')}")
        print(f"  costs={ab.get('costs')}")
else:
    print(f"File not found: {path}")
