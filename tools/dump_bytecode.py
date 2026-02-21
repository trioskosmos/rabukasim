import json
import os

try:
    print("Loading compiled cards...")
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    target_card = "PL!S-bp2-005-P"
    card_data = None

    print(f"Searching for {target_card}...")
    for key, value in data['member_db'].items():
        if target_card in value.get('card_no', ''):
            card_data = value
            break
    
    if not card_data:
        print(f"Card {target_card} not found!")
        exit(1)

    print(f"Found card: {card_data.get('name')}")
    bytecode = card_data['abilities'][0]['bytecode']
    
    output_path = 'reports/bytecode_decode.txt'
    with open(output_path, 'w', encoding='utf-8') as out:
        out.write(f"Card: {card_data.get('card_no')} - {card_data.get('name')}\n")
        out.write(f"Bytecode length: {len(bytecode)}\n")
        out.write(f"Raw Ability: {card_data.get('ability_text')}\n\n")
        
        out.write("--- Bytecode Dump ---\n")
        out.write("IDX | OP  | V          | A          | A (HEX)    | S    \n")
        out.write("----|-----|------------|------------|------------|------\n")
        
        for i in range(0, len(bytecode), 4):
            if i+3 >= len(bytecode):
                out.write(f"Incomplete chunk at {i}: {bytecode[i:]}\n") 
                break
                
            op = bytecode[i]
            v = bytecode[i+1]
            a = bytecode[i+2]
            s = bytecode[i+3]
            
            # Helper for Opcode Names (Partial)
            op_name = str(op)
            if op == 41: op_name = "LOOK_AND_CHOOSE (41)"
            
            out.write(f"[{i//4:2d}] | {op_name:<20} | {v:<10} | {a:<10} | 0x{a:08X} | {s:<4}\n")

    print(f"Dumped bytecode to {output_path}")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error: {e}")
