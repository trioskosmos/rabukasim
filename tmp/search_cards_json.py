import json
import os

def search():
    path = "data/cards_compiled.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    db = data.get("member_db", {})
    query = "bp2-001"
    
    results = {}
    for cid, card in db.items():
        if query in card.get("card_no", ""):
            results[cid] = card
            
    with open("tmp/search_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Found {len(results)} matches. Results saved to tmp/search_results.json")

if __name__ == "__main__":
    search()
