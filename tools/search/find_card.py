import json

with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)


def find_card(card_no):
    for db_name in ["member_db", "live_db"]:
        for card_id, card in data.get(db_name, {}).items():
            if card.get("card_no") == card_no:
                return card
    return None


card = find_card("PL!-pb1-013-R")
if card:
    with open("tmp_card.json", "w", encoding="utf-8") as f:
        json.dump(card, f, indent=2, ensure_ascii=False)
    print("Saved to tmp_card.json")
else:
    print("Card not found")
