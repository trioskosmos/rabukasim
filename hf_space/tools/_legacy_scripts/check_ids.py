import json

with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
    d = json.load(f)

c = d["member_db"]["129"]
print(f"ID 129: {c['card_no']}")
print(f"Name: {c['name']}")
print(f"Ability: {c['ability_text']}")

c = d["member_db"]["130"]
print(f"ID 130: {c['card_no']}")
print(f"Name: {c['name']}")
print(f"Ability: {c['ability_text']}")
