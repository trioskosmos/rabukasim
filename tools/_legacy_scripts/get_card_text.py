import json
import sys


def get_text(card_no):
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Search member_db
    for cid, card in data.get("member_db", {}).items():
        if card.get("card_no") == card_no:
            print(f"Card: {card_no} (ID {cid})")
            print("-" * 20)
            print(f"Ability Text:\n{card.get('ability_text')}")
            print("-" * 20)
            print(f"Original Text:\n{card.get('original_text')}")
            return

    # Search live_db
    for cid, card in data.get("live_db", {}).items():
        if card.get("card_no") == card_no:
            print(f"Card: {card_no} (ID {cid})")
            print("-" * 20)
            print(f"Ability Text:\n{card.get('ability_text')}")
            print("-" * 20)
            print(f"Original Text:\n{card.get('original_text')}")
            return

    print("Card not found.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        get_text(sys.argv[1])
    else:
        print("Usage: python get_card_text.py <card_no>")
