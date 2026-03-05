import json
with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    cards = json.load(f)
if "4199" in cards:
    c = cards["4199"]
    print(f"ID 4199 - {c.get('card_number')}: {c.get('ability_text_jp', '')}")
    print(json.dumps(c.get("abilities", []), indent=2, ensure_ascii=False))
else:
    print("Card 4199 not found in compiled data.")
