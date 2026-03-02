import json
import os

def find_cards_by_opcodes(opcodes):
    compiled_path = os.path.join("data", "cards_compiled.json")
    with open(compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    results = {}
    for op in opcodes:
        results[op] = []
        
    member_db = data.get("member_db", {})
    live_db = data.get("live_db", {})
    
    for db in [member_db, live_db]:
        for card_id, card_data in db.items():
            if "abilities" in card_data:
                for ab in card_data["abilities"]:
                    bytecode = ab.get("bytecode", [])
                    # Check every 5 words (instruction boundary)
                    for i in range(0, len(bytecode), 5):
                        op = bytecode[i]
                        if op in opcodes:
                            results[op].append((card_id, card_data.get("card_no"), ab.get("pseudocode")))
                            break # Found this opcode in this ability
                            
    for op, found in results.items():
        print(f"=== Opcode {op} ===")
        if not found:
            print("No cards found.")
        else:
            for f in found[:3]: # Show top 3
                print(f"ID: {f[0]}, Card No: {f[1]}")
                print(f"Pseudocode: {f[2]}")
                print("-" * 10)
        print("\n")

if __name__ == "__main__":
    opcodes_to_find = [35, 36, 40, 42, 47, 49, 61, 76, 93, 94, 201, 214, 250, 245, 247]
    find_cards_by_opcodes(opcodes_to_find)
