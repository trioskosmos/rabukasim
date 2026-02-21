import json
import sys


def get_raw_card(card_no):
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for k, v in data.items():
        if v.get("card_no") == card_no:
            print(json.dumps(dict(v), indent=2, ensure_ascii=False))
            return
    print("Not found")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        get_raw_card(sys.argv[1])
    else:
        print("Usage: python get_raw_card.py <card_no>")
