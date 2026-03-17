import json


def list_sd1_cards():
    with open("engine/data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    card_ids = sorted(list(data.keys()))

    # Filter for SD1
    sd1_cards = [c for c in card_ids if "sd1" in c]

    for c in sd1_cards:
        print(c)


if __name__ == "__main__":
    list_sd1_cards()
