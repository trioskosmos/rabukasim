import json
import os

def generate_new_mapping():
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    mapping = {}
    
    # Process members
    for card_id_str, card in data.get("member_db", {}).items():
        mapping[card["card_no"]] = int(card_id_str)
    
    # Process lives
    for card_id_str, card in data.get("live_db", {}).items():
        mapping[card["card_no"]] = int(card_id_str)
        
    os.makedirs('reports', exist_ok=True)
    with open('reports/new_id_map.json', 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(mapping)} mappings to reports/new_id_map.json")

if __name__ == "__main__":
    generate_new_mapping()
