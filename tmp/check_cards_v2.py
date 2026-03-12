import json
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def check():
    path = "data/cards_compiled.json"
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    db = data.get("member_db", {})
    
    # Check card 4511 (PL!S-bp2-001-R)
    c4511 = db.get("4511")
    if c4511:
        print("--- Card 4511 (PL!S-bp2-001-R) ---")
        print(f"Name: {c4511.get('name')}")
        print(f"Original Text (JP): {c4511.get('original_text')}")
        print(f"Original Text EN: {c4511.get('original_text_en')}")
        print(f"Ability Text (Pseudocode): {c4511.get('ability_text')}")
    else:
        print("Card 4511 not found in member_db")
        
    # Search for the user's specific "half-translated" string
    user_str = "ブレードブレードブレードを得る"
    print(f"\nSearching for cards containing: '{user_str}'")
    found = 0
    for cid, card in db.items():
        text = str(card.get('original_text', '')) + str(card.get('ability_text', ''))
        if user_str in text:
            print(f"Found in Card {cid} ({card.get('card_no')}): {card.get('name')}")
            print(f"  Ability Text: {card.get('ability_text')}")
            found += 1
            if found > 5: break

if __name__ == "__main__":
    check()
