import json
with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)
member_db = data.get("member_db", {})
if "4199" in member_db:
    c = member_db["4199"]
    print(f"ID 4199 - {c.get('card_number')}: {c.get('ability_text_jp', '')}")
    print(json.dumps(c.get("abilities", []), indent=2, ensure_ascii=False))
else:
    print("Card 4199 not found in member_db.")
