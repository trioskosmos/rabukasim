import json
import os


def read_card_source():
    path = "data/cards.json"
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Structure: { "members": [ ... ] } or list?
    # Loader says: loader.load() returns m, l, e.
    # Usually structure is dict with "members" key?
    # Let's inspect structure type.

    if isinstance(data, list):
        print("Data is list (legacy format?)")
        members = data
    elif isinstance(data, dict):
        members = data.get("members", [])
    else:
        print("Unknown data format")
        return

    target = "PL!N-bp1-002-P"
    for card in members:
        if card.get("card_no") == target:
            print(f"Found Source for {target}:")
            # print(json.dumps(card, indent=2, ensure_ascii=False))
            # Just print abilities to be concise
            for i, ab in enumerate(card.get("abilities", [])):
                print(f"Ability {i}: {ab}")
            return

    print("Card not found in source.")


if __name__ == "__main__":
    read_card_source()
