import json

with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("MEMBER CARDS:")
for k, v in data["member_db"].items():
    if "PL!N" in v["card_no"]:
        print(f"ID: {k}, NO: {v['card_no']}, NAME: {v['name']}")

print("\nLIVE CARDS:")
for k, v in data["live_db"].items():
    if "PL!N" in v["card_no"]:
        print(f"ID: {k}, NO: {v['card_no']}, NAME: {v['name']}")
