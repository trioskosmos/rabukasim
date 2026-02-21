import json
import os

def lookup():
    cards_path = "data/cards.json"
    if not os.path.exists(cards_path):
        print("cards.json not found")
        return

    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    target_id = "PL!SP-bp4-015-N"
    card = data.get(target_id)
    
    print(f"Details for {target_id}:")
    if card:
        print(json.dumps(card, indent=2, ensure_ascii=False))
    else:
        print("Card ID not found in cards.json")

    print("\n--- Searching for 'Miyashita Ai' (宮下 愛) ---")
    ai_matches = []
    for cid, cdata in data.items():
        name = cdata.get("name", "")
        # Check name or ability text or anything descriptive
        if "宮下" in name or "愛" in name:
             ai_matches.append(f"{cid}: {name}")
    
    for match in ai_matches[:20]:
        print(match)

if __name__ == "__main__":
    lookup()
