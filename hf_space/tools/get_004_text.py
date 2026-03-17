import json


def get_004_text():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    results = {}
    for card_no, data in cards.items():
        if "004" in card_no:
            results[card_no] = {"name": data.get("name"), "ability": data.get("ability")}

    with open("reports/all_004_cards.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    get_004_text()
