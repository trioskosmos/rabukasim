import json
import os


def find_card():
    path = "data/cards_compiled.json"
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    target = "PL!N-bp1-002-P"

    # Check member_db
    for cid, card in data.get("member_db", {}).items():
        if card.get("card_no") == target:
            print(f"Found {target} in member_db: ID = {cid}")
            for ab in card.get("abilities", []):
                print(f"Ability: {ab.get('trigger')} Bytecode: {ab.get('bytecode')}")
            # Continue searching
            # return int(cid)

    print("Card not found.")


if __name__ == "__main__":
    find_card()
