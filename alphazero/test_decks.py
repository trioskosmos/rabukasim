import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alphazero.v1_benchmark import load_tournament_decks

def test_deck_loading():
    print("Testing tournament deck loading...")
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        full_db = json.load(f)
    
    decks = load_tournament_decks(full_db)
    print(f"Loaded {len(decks)} decks.")
    for d in decks:
        print(f"Deck: {d['name']}, Members: {len(d['members'])}, Live: {len(d['lives'])}, Energy: {len(d['energy'])}")
    
    if not decks:
        print("ERROR: No decks loaded!")
    else:
        print("Deck loading SUCCESSFUL.")

if __name__ == "__main__":
    test_deck_loading()
