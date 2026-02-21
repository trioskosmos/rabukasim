import json

with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)

card_no = "PL!S-PR-013-PR"
card = None
for v in data["member_db"].values():
    if v["card_no"] == card_no:
        card = v
        break

if card:
    print(f"Card: {card['name']} ({card_no})")
    print("Abilities:")
    for i, ab in enumerate(card.get("abilities", [])):
        print(f"  [{i}] Trigger: {ab.get('trigger')}")
        print(f"      Conditions: {ab.get('conditions')}")
        print(f"      Costs: {ab.get('costs')}")
        print(f"      Effects: {ab.get('effects')}")
else:
    print(f"Card {card_no} not found.")
