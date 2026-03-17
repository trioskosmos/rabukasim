import json

with open("data/cards_compiled.json", encoding="utf-8") as f:
    data = json.load(f)

print("--- Searching for Sum 19 / Card 19 ---")
for cid, card in data["member_db"].items():
    txt = card.get("original_text", "")
    # Look for "19" or "１９" and "手札" or "手札をすべて公開"
    if ("19" in txt or "１９" in txt) and ("手札" in txt):
        print(f"ID {cid}: {card.get('card_no')} - {card.get('name')} - {txt}")
