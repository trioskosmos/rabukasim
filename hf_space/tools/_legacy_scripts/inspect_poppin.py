import json
import os

path = "engine/data/cards_compiled.json"
if not os.path.exists(path):
    print("File not found")
    exit(1)

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

card = data["live_db"].get("30047")
if not card:
    print("Card 30047 not found")
else:
    abilities = card.get("abilities", [])
    if not abilities:
        print("No abilities found")
    else:
        for i, ab in enumerate(abilities):
            print(f"Ability {i}:")
            print(f"  Trigger: {ab.get('trigger')}")
            print(f"  Bytecode: {ab.get('bytecode')}")
            print(f"  Raw: {ab.get('raw_text')}")
