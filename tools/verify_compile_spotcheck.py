import json
import os


def find_card():
    path = "data/cards_compiled.json"
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    card_no_to_find = "PL!-PR-001-PR"

    for db_name in ["member_db", "live_db"]:
        db = data.get(db_name, {})
        for cid, card_data in db.items():
            if card_data.get("card_no") == card_no_to_find:
                print(f"Found in {db_name} with ID {cid}")
                print(json.dumps(card_data, indent=2, ensure_ascii=False))
                return

    print(f"Card {card_no_to_find} not found in compiled database")


if __name__ == "__main__":
    find_card()
