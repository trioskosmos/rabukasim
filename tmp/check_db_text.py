
import os
import sys

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.game.data_loader import CardDataLoader

def check():
    cards_path = os.path.join(PROJECT_ROOT, "data", "cards.json")
    print(f"Loading card data from: {cards_path}")
    loader = CardDataLoader(cards_path)
    members, lives, energy = loader.load()
    
    # Check a few cards that are known to have English translations in compiled JSON
    # From earlier grep: ID 4511 (PL!S-bp2-001-R) should have it.
    
    test_ids = [4511, 10, 415]
    for cid in test_ids:
        if cid in members:
            m = members[cid]
            print(f"--- Card {cid} ({m.card_no}) ---")
            print(f"Name: {m.name}")
            print(f"Original Text: {m.original_text[:50]}...")
            print(f"Original Text EN: {getattr(m, 'original_text_en', 'MISSING')[:50]}...")
        elif cid in lives:
            l = lives[cid]
            print(f"--- Live Card {cid} ({l.card_no}) ---")
            print(f"Name: {l.name}")
            print(f"Original Text EN: {getattr(l, 'original_text_en', 'MISSING')[:50]}...")
        else:
            print(f"--- Card {cid} NOT FOUND in DB ---")

if __name__ == "__main__":
    check()
