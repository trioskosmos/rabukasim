import json


def find_card_text():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    target = "PL!S-pb1-005-R"
    if target in data:
        card = data[target]
        print(f"Name: {card.get('name')}")
        print(f"Ability: {card.get('ability')}")
    else:
        # Try finding by partial ID
        for cid, card in data.items():
            if "pb1-005-R" in cid:
                print(f"Found ID: {cid}")
                print(f"Name: {card.get('name')}")
                print(f"Ability: {card.get('ability')}")
                break


if __name__ == "__main__":
    find_card_text()
