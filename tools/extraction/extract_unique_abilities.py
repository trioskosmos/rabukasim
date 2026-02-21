import json
import os


def main():
    raw_path = "engine/data/cards.json"
    override_path = "data/manual_pseudocode.json"
    output_path = "unique_abilities_for_mapping.json"

    if not os.path.exists(raw_path):
        print("Missing engine/data/cards.json")
        return

    with open(raw_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    overrides = {}
    if os.path.exists(override_path):
        with open(override_path, "r", encoding="utf-8") as f:
            overrides = json.load(f)

    # Dictionary: JP Text -> List of Card Numbers
    unique_map = {}

    for card_no, data in cards.items():
        # Skip cards already in overrides
        if card_no in overrides:
            continue

        ability_text = data.get("ability", "")
        if not ability_text:
            continue

        if ability_text not in unique_map:
            unique_map[ability_text] = []
        unique_map[ability_text].append(card_no)

    print(f"Found {len(unique_map)} unique Japanese abilities requiring mapping.")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique_map, f, ensure_ascii=False, indent=2)

    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
