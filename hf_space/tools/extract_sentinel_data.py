import json


def extract_sentinel_data():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        pseudo = json.load(f)

    sentinels = ["PL!N-bp5-001-AR", "PL!N-bp5-002-AR", "PL!N-bp5-005-AR", "PL!N-bp3-008-P", "PL!SP-bp5-004-P"]

    results = {}
    for card_no in sentinels:
        card_data = cards.get(card_no)
        pseudo_data = pseudo.get(card_no, "N/A")

        results[card_no] = {
            "name": card_data.get("name", "Unknown") if card_data else "Unknown",
            "jp_ability": card_data.get("ability", "N/A") if card_data else "N/A",
            "pseudocode": pseudo_data.get("pseudocode", "N/A") if isinstance(pseudo_data, dict) else "N/A",
        }

    with open("reports/sentinel_verification.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    extract_sentinel_data()
