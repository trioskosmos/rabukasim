import json

with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
    db = json.load(f)

for mid, card in db["member_db"].items():
    if "sd1-008" in card["card_no"]:
        print(f"ID: {mid} | No: {card['card_no']} | Name: {card['name']}")
        for i, ab in enumerate(card["abilities"]):
            print(f"  Ability {i}: Trigger={ab['trigger']}")
            for j, eff in enumerate(ab["effects"]):
                print(f"    Effect {j}: Type={eff['effect_type']} Value={eff.get('value')}")
