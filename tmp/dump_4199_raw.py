import json
with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)
member_db = data.get("member_db", {})
if "4199" in member_db:
    c = member_db["4199"]
    for ab in c.get("abilities", []):
        print(f"Trigger: {ab.get('trigger')}")
        print(f"Bytecode: {ab.get('bytecode')}")
else:
    print("Card 4199 not found in member_db.")
