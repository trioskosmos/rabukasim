import json
import os

def find_card_by_pseudocode(pseudocode_part):
    compiled_path = os.path.join("data", "cards_compiled.json")
    with open(compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    found = []
    member_db = data.get("member_db", {})
    for card_id, card_data in member_db.items():
        if "abilities" in card_data:
            for ab in card_data["abilities"]:
                if "TRIGGER: CONSTANT" in ab.get("pseudocode", "") and pseudocode_part in ab.get("pseudocode", ""):
                    found.append((card_id, card_data.get("card_no"), ab.get("pseudocode")))
                    
    for f in found[:20]:
        print(f"ID: {f[0]}, Card No: {f[1]}")
        print(f"Pseudocode: {f[2]}")
        print("-" * 20)

if __name__ == "__main__":
    find_card_by_pseudocode("ADD_BLADES")
