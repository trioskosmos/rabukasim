import json
import os

def check():
    path = 'data/cards_compiled.json'
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    low_count = 0
    high_count = 0
    
    for cid, card in data.items():
        if 'abilities' in card:
            for ab in card['abilities']:
                bc = ab.get('bytecode', [])
                for i in range(0, len(bc), 5):
                    if i + 3 < len(bc):
                        if (bc[i+2] & 536870912) != 0:
                            low_count += 1
                        if (bc[i+3] & 536870912) != 0:
                            high_count += 1
    
    print(f"Bit 29 in Low Word (Index 2): {low_count}")
    print(f"Bit 29 in High Word (Index 3/Bit 61): {high_count}")

if __name__ == "__main__":
    check()
