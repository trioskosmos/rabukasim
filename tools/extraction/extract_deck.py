import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.getcwd())

from engine.game.deck_utils import UnifiedDeckParser


def extract_deck():
    # Load card DB
    db_path = "data/cards.json"
    card_db = {}
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            card_db = json.load(f)
    else:
        print(f"Error: {db_path} not found.")
        return

    # Load extraction content
    content_path = "tests/decktest.txt"
    if not os.path.exists(content_path):
        print(f"Error: {content_path} not found.")
        # Try finding it in project root
        content_path = os.path.join(os.getcwd(), "tests/decktest.txt")

    try:
        with open(content_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Failed to read {content_path}: {e}")
        return

    # Parse decks
    parser = UnifiedDeckParser(card_db)
    results = parser.extract_from_content(content)

    if not results:
        print("No cards found.")
        return

    for deck in results:
        print(f"\nDeck: {deck['name']}")
        print(f"Total Main: {len(deck['main'])}")
        print(f"Total Energy: {len(deck['energy'])}")
        
        # Print first few for verification
        for cid in sorted(set(deck['main']))[:5]:
            count = deck['main'].count(cid)
            print(f"  {cid} x{count}")


if __name__ == "__main__":
    extract_deck()
