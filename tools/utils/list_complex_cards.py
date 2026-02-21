import json
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.ability import AbilityParser

from tools.master_validator import MasterValidator


def main():
    cards_path = "data/cards.json"
    validator = MasterValidator(cards_path)
    complex_cards = []

    for card in validator.cards.values():
        text = card.get("ability", "")
        abilities = []
        if text:
            abilities = AbilityParser.parse_ability_text(text)
        faq_count = len(card.get("faq", []))
        score = validator._calculate_score(text, abilities, faq_count)

        if score >= 110:
            tier = "SSS" if score >= 123 else "SS"
            complex_cards.append(
                {
                    "id": card.get("card_no", "N/A"),
                    "name": card.get("name"),
                    "score": score,
                    "tier": tier,
                    "faq_count": faq_count,
                    "ability": text,
                    "faq": card.get("faq", []),
                }
            )

    complex_cards.sort(key=lambda x: x["score"], reverse=True)

    if not complex_cards:
        print("No complex cards found.")
        return

    c = complex_cards[0]
    print(f"ID: {c['id']}")
    print(f"Name: {c['name']}")
    print(f"Ability:\n{c['ability']}")
    print(f"FAQ Count: {c['faq_count']}")
    print(json.dumps(c["faq"], indent=2, ensure_ascii=False))

    # Also list top 5
    ids_to_test = [x["id"] for x in complex_cards[:5]]
    print(f"IDs: {ids_to_test}")


if __name__ == "__main__":
    main()
