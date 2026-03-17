import json
from collections import Counter


def extract_abilities():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    abilities = []
    for card_id, card in cards.items():
        if "ability" in card and card["ability"]:
            abilities.append(card["ability"])
        # Also check card_variants if they exist, but cards.json seems to be flat

    unique_abilities = Counter(abilities)

    # Sort by frequency
    sorted_abilities = sorted(unique_abilities.items(), key=lambda x: x[1], reverse=True)

    with open("unique_abilities.json", "w", encoding="utf-8") as f:
        json.dump(sorted_abilities, f, ensure_ascii=False, indent=4)

    print(f"Extracted {len(sorted_abilities)} unique abilities from {len(cards)} cards.")


if __name__ == "__main__":
    extract_abilities()
