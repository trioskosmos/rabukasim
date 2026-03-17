import json


def find_has_choice_cards():
    with open("docs/full_ability_coverage.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for card in data.get("with_ability", []):
        parsed = card.get("parsed")
        if parsed and "HAS_CHOICE" in parsed.get("conditions", []):
            print(f"Card {card['id']} ({card['name']}) has HAS_CHOICE")
            print(f"Text: {card['ability_text']}")

    for card in data.get("with_ability", []):
        parsed = card.get("parsed")
        if parsed and "OPPONENT_CHOICE" in parsed.get("conditions", []):
            print(f"Card {card['id']} ({card['name']}) has OPPONENT_CHOICE")
            print(f"Text: {card['ability_text']}")


if __name__ == "__main__":
    find_has_choice_cards()
