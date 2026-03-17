import json
from collections import defaultdict


def map_abilities_to_cards():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    ability_map = defaultdict(list)
    for card_id, card in cards.items():
        if "ability" in card and card["ability"]:
            ability_map[card["ability"]].append(card["card_no"])

    # Sort by frequency (descending)
    sorted_abilities = sorted(ability_map.items(), key=lambda x: len(x[1]), reverse=True)

    output = []
    for ability, card_nos in sorted_abilities:
        output.append(
            {
                "ability": ability,
                "count": len(card_nos),
                "sample_cards": card_nos[:5],  # Just show a few samples
            }
        )

    with open("ability_to_card_map.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print(f"Mapped {len(sorted_abilities)} unique abilities to cards.")


if __name__ == "__main__":
    map_abilities_to_cards()
