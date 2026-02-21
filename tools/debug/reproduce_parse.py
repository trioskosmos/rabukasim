import json
import os
import sys

# Mimic server.py setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), "tools"))

try:
    from deck_extractor import extract_deck_data

    print("Import successful")
except ImportError:
    print("Import failed")
    sys.exit(1)


def test():
    # Load DB
    with open("data/cards.json", "r", encoding="utf-8") as f:
        card_db = json.load(f)

    # Load Deck
    with open("tests/decktest.txt", "r", encoding="utf-8") as f:
        content = f.read()

    main, energy, counts, errors = extract_deck_data(content, card_db)

    print(f"Main: {len(main)}")
    print(f"Energy: {len(energy)}")
    print(f"Errors: {errors}")

    if len(main) == 0:
        print("FAIL: No main deck cards found.")
    else:
        print("SUCCESS: Parsed cards.")


if __name__ == "__main__":
    test()
