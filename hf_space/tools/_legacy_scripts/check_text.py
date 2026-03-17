import json

with open("engine/data/cards.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
    compiled = json.load(f)

# Check raw
if "PL!-sd1-008-SD" in raw:
    print("RAW PL!-sd1-008-SD:")
    print(f"  ability: {raw['PL!-sd1-008-SD'].get('ability', 'N/A')}")

# Check compiled
for k, v in compiled["member_db"].items():
    if v["card_no"] == "PL!-sd1-008-SD":
        print(f"COMPILED PL!-sd1-008-SD (ID {k}):")
        print(f"  ability_text: {v.get('ability_text', 'N/A')}")
        break
