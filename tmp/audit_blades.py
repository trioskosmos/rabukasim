
import json

def audit():
    try:
        with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    results = []
    
    # Opcode 224: C_COUNT_BLADES
    # Opcode 242: C_BLADE_COMPARE
    
    for ctype in ['member_db', 'live_db']:
        db_section = data.get(ctype, {})
        # Depending on structure, db_section might be a dict or a list
        # If it's the member_db, it's often a dict of {id: card_data}
        card_list = db_section.values() if isinstance(db_section, dict) else db_section
        
        for card in card_list:
            card_no = card.get('card_no', card.get('id', 'Unknown'))
            for ab_idx, ab in enumerate(card.get('abilities', [])):
                sources = []
                
                # Check Conditions
                for cond_idx, cond in enumerate(ab.get('conditions', [])):
                    ct = cond.get('condition_type')
                    if ct in [224, 242]:
                        sources.append(f"Condition[{cond_idx}] Type={ct}")
                
                # Check Bytecode
                bc = ab.get('bytecode', [])
                if isinstance(bc, list):
                    for i in range(0, len(bc)-4, 5):
                        op = bc[i]
                        if op in [224, 242]:
                            sources.append(f"Bytecode[{i//5}] Op={op}")
                
                if sources:
                    results.append(f"Card {card_no} Ability {ab_idx}: " + ", ".join(sources))

    if not results:
        print("No usages of 224 or 242 found.")
    for r in results:
        print(r)

if __name__ == "__main__":
    audit()
