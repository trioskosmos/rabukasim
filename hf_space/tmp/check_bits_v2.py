import json
import os

def check():
    path = 'data/cards_compiled.json'
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    counts = {2: 0, 3: 0}
    
    # Iterate through all databases
    for db_name in ["member_db", "live_db", "energy_db"]:
        db = data.get(db_name, {})
        for cid, card in db.items():
            for ab in card.get('abilities', []):
                bc = ab.get('bytecode', [])
                for i in range(0, len(bc), 5):
                    if i + 3 < len(bc):
                        attr_low = bc[i+2]
                        attr_high = bc[i+3]
                        
                        # Check Bit 29 in Low Word
                        if (attr_low & 536870912) != 0:
                            counts[2] += 1
                        # Check Bit 29 in High Word (Bit 61)
                        if (attr_high & 536870912) != 0:
                            counts[3] += 1
    
    print(f"Total instructions with Bit 29 in Low Word: {counts[2]}")
    print(f"Total instructions with Bit 29 in High Word (Bit 61): {counts[3]}")

if __name__ == "__main__":
    check()
