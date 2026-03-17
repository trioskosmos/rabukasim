import json


def inspect_cards():
    ids = ["PL!-pb1-004-P＋", "PL!-PR-007-PR", "PL!N-bp3-003-P"]
    with open("engine/data/cards.json", encoding="utf-8") as f:
        data = json.load(f)

    for cid, c in data.items():
        if c.get("card_no") in ids:
            print(f"\n=== {c.get('card_no')} ({c.get('name')}) ===")
            print(f"Trigger: {c.get('ability')}")


if __name__ == "__main__":
    inspect_cards()
