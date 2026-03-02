import json
import sys


def inspect_card(query):
    with open("data/cards_compiled.json", encoding="utf-8") as f:
        data = json.load(f)

    for cid, card in data["member_db"].items():
        if query == cid or query == card.get("card_no"):
            print(f"--- CARD FOUND: ID {cid} ---")
            print(f"No: {card.get('card_no')}")
            print(f"Name: {card.get('name')}")
            print(f"Text: {card.get('original_text')}")
            print(f"Abilities: {json.dumps(card.get('abilities'), indent=2, ensure_ascii=False)}")
            return

    # Search by text if no direct match
    print(f"--- SEARCHING FOR TEXT '{query}' ---")
    for cid, card in data["member_db"].items():
        txt = card.get("original_text", "")
        if query in txt:
            print(f"ID {cid}: {card.get('card_no')} - {card.get('name')} - {txt[:50]}...")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_card(sys.argv[1])
    else:
        print("Usage: python inspect_card.py <ID|CARD_NO|TEXT>")
