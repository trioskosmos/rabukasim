import json


def extract_bp5_all():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        pseudo = json.load(f)

    results = {}
    for card_no, data in cards.items():
        if "bp5" in card_no:
            results[card_no] = {
                "name": data.get("name"),
                "ability": data.get("ability"),
                "p": pseudo.get(card_no, {}).get("pseudocode", "MISSING"),
            }

    with open("reports/bp5_deep_audit_raw.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    extract_bp5_all()
