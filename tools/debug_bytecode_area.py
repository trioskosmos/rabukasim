import json
import os

def check_card_bytecode(card_no):
    compiled_path = "data/cards_compiled.json"
    if not os.path.exists(compiled_path):
        print(f"Error: {compiled_path} not found")
        return

    with open(compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    cards = data.get("cards", [])
    card = next((c for c in cards if c["card_no"] == card_no), None)
    
    if not card:
        print(f"Card {card_no} not found, showing first card: {cards[0]['card_no']}")
        card = cards[0]

    print(f"--- Bytecode for {card['card_no']} ---")
    
    for i, ability in enumerate(card.get("abilities", [])):
        bc = ability.get("bytecode", [])
        print(f"Ability {i}: {bc}")
        
        # Bytecode is groups of 4: [op, val, attr, packed_slot]
        for j in range(0, len(bc), 4):
            instr = bc[j:j+4]
            if len(instr) < 4: continue
            
            op, val, attr, packed_slot = instr
            
            # Area index is in packed_slot bits 29-31
            # In Python, we can extract this by masks
            u_slot = packed_slot & 0xFFFFFFFF
            area_idx = (u_slot >> 29) & 0x07
            
            print(f"  Instr {j//4}: op={op}, val={val}, slot_hex={hex(u_slot)}, area_idx={area_idx}")

if __name__ == "__main__":
    import sys
    card_no = sys.argv[1] if len(sys.argv) > 1 else "PL!-pb1-001-R"
    check_card_bytecode(card_no)
