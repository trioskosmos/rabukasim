import json

def find_orphaned_opcodes():
    with open('data/metadata.json', 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        card_data = json.load(f)
        
    used_ops = set()
    for card in card_data.get('member_db', {}).values():
        for ab in card.get('abilities', []):
            bc = ab.get('bytecode', [])
            for i in range(0, len(bc), 4):
                used_ops.add(bc[i])
                
    all_ops = {v: k for k, v in metadata['opcodes'].items()}
    orphaned = []
    for op_val, name in all_ops.items():
        if op_val not in used_ops and op_val not in [0, 1, 2, 3]: # Ignore basic flow
            orphaned.append(f"{name} ({op_val})")
            
    print("Orphaned Opcodes (Defined but not used in cards):")
    for o in sorted(orphaned):
        print(f"- {o}")

if __name__ == "__main__":
    find_orphaned_opcodes()
