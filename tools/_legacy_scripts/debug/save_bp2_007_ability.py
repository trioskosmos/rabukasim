import json

with open("engine/data/cards.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    for k, v in data.items():
        if v.get("card_no") == "PL!S-bp2-007-P":
            with open("bp2_007_ability.txt", "w", encoding="utf-8") as f2:
                f2.write(v.get("ability"))
            break
