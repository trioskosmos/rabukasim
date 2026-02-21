import json


def search_cards():
    cards_path = "engine/data/cards.json"
    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    print("Searching for Life Lead patterns...")
    for cid, card in cards.items():
        text = card.get("ability", "")
        if "ライフ" in text or "Life" in text:
            print(f"[{card.get('card_no')}] {text[:50]}...")


if __name__ == "__main__":
    search_cards()
