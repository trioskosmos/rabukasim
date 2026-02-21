"""
Read through cards systematically and build precise ability catalog.
"""

import json


def main():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    cards = list(data.values())

    # Focus on cards with abilities
    cards_with_abilities = [c for c in cards if c.get("ability", "")]

    print(f"Total cards with abilities: {len(cards_with_abilities)}")
    print("\n" + "=" * 80)

    # Read through first 50 systematically
    for i, card in enumerate(cards_with_abilities[:50], 1):
        print(f"\n### Card #{i}: {card.get('card_no', 'N/A')} ({card.get('name', 'Unknown')})")
        print(f"Type: {card.get('type', 'N/A')}")
        print("\n**Ability**:")
        print(card.get("ability", "None"))
        print("\n" + "-" * 80)

        if i % 10 == 0:
            input(f"\n[Processed {i} cards - Press Enter to continue...]")


if __name__ == "__main__":
    main()
