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
    cards_with_bit_29 = []
    
    for cid, card in data.items():
        if 'abilities' in card:
            for ab in card['abilities']:
                bc = ab.get('bytecode', [])
                for i in range(0, len(bc), 5):
                    if i + 3 < len(bc):
                        if bc[i+2] == 536870912:
                            counts[2] += 1
                            cards_with_bit_29.append(cid)
                        if bc[i+3] == 536870912:
                            counts[3] += 1
    
    print(f"Index 2 (Bit 29): {counts[2]}")
    print(f"Index 3 (Bit 61): {counts[3]}")
    if cards_with_bit_29:
        print(f"Sample cards with Bit 29: {cards_with_bit_29[:10]}")

if __name__ == "__main__":
    check()
