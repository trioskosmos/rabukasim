import json


def check_card_types():
    with open("engine/data/cards.json", encoding="utf-8") as f:
        data = json.load(f)

    ids = ["PL!S-pr-001-PR", "PL!S-pr-002-PR", "PL!S-pr-003-PR", "PL!S-pr-004-PR"]

    for cid, c in data.items():
        if c.get("card_no") in ids:
            print(f"{c.get('card_no')}: type={c.get('card_type')}")


if __name__ == "__main__":
    check_card_types()
