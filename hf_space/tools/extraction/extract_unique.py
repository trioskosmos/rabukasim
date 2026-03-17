import json
import os


def main():
    compiled_path = "data/cards_compiled.json"
    raw_path = "engine/data/cards.json"

    if not os.path.exists(compiled_path) or not os.path.exists(raw_path):
        print("Missing data files.")
        return

    with open(compiled_path, "r", encoding="utf-8") as f:
        compiled_data = json.load(f)
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_cards = json.load(f)

    unique_abilities = {}  # ability_raw -> (bytecode, example_card_no)

    def process_db(db):
        for card_id, card_data in db.items():
            card_no = card_data.get("card_no")
            raw_text = raw_cards.get(card_no, {}).get("ability", "")
            if not raw_text:
                continue

            # Simple split if multiple abilities (imprecise but helpful for initial look)
            # Actually, compiled data has abilities separated.
            abilities_compiled = card_data.get("abilities", [])
            for i, ab in enumerate(abilities_compiled):
                ab_raw = ab.get("raw_text", "")
                if ab_raw not in unique_abilities:
                    unique_abilities[ab_raw] = (ab.get("bytecode", []), card_no)

    if "member_db" in compiled_data:
        process_db(compiled_data["member_db"])
    if "live_db" in compiled_data:
        process_db(compiled_data["live_db"])

    results = []
    for raw, (bc, card) in unique_abilities.items():
        results.append({"raw": raw, "bytecode": bc, "example": card})

    # Sort results to help processing
    results.sort(key=lambda x: x["example"])

    with open("unique_abilities_audit.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(results)} unique abilities.")


if __name__ == "__main__":
    main()
