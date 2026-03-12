import os
import sys
import json

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.curdir)
sys.path.insert(0, PROJECT_ROOT)

from engine.game.data_loader import CardDataLoader

def check():
    cards_path = os.path.join("data", "cards.json")
    print(f"Loading from {cards_path}")
    loader = CardDataLoader(cards_path)
    members, lives, energy = loader.load()
    
    print(f"Loaded {len(members)} members")
    
    # Check PL!S-bp2-001-R (ID 4511)
    target_id = 4511
    if target_id in members:
        m = members[target_id]
        print(f"Card {target_id} ({m.card_no}):")
        print(f"  original_text: {m.original_text[:50]}...")
        print(f"  original_text_en: '{m.original_text_en}'")
        if not m.original_text_en:
            print("  WARNING: original_text_en is EMPTY!")
    else:
        print(f"Card {target_id} not found in members!")
        # Try to find by card_no
        for mid, m in members.items():
            if m.card_no == "PL!S-bp2-001-R":
                print(f"Found by card_no at ID {mid}:")
                print(f"  original_text_en: '{m.original_text_en}'")
                break

if __name__ == "__main__":
    check()
