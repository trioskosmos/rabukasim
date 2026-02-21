import json
import os

def analyze_opcodes():
    compiled_path = 'data/cards_compiled.json'
    scenario_path = 'engine_rust_src/data/scenarios.json'
    
    with open(compiled_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        member_db = data['member_db']
    
    with open(scenario_path, 'r', encoding='utf-8') as f:
        scenarios = json.load(f)['scenarios']
    
    # 1. Collect all unique opcodes in the entire DB
    all_opcodes_in_db = set()
    for card in member_db.values():
        for ab in card.get('abilities', []):
            bc = ab.get('bytecode', [])
            # Heuristic: opcodes are usually at indices 0, 4, 8... if 4-byte aligned
            # But let's just collect all unique values in the byte stream that match known opcodes
            for byte in bc:
                if 1 <= byte <= 90 or 200 <= byte <= 240:
                    all_opcodes_in_db.add(byte)
    
    # 2. Collect opcodes in cards that have scenarios
    covered_card_ids = {s['id'].split('_')[0] for s in scenarios}
    covered_opcodes = set()
    for cid in covered_card_ids:
        # Map scenario ID (numeric or string) to card in DB
        # Scenario IDs in scenarios.json are like "PL!SP-bp4-017-N" or "1179"
        card = member_db.get(cid)
        if not card:
            # Try to find by card_no
            card = next((c for c in member_db.values() if c['card_no'] == cid), None)
            
        if card:
            for ab in card.get('abilities', []):
                bc = ab.get('bytecode', [])
                for byte in bc:
                    if 1 <= byte <= 90 or 200 <= byte <= 240:
                        covered_opcodes.add(byte)

    print(f"Unique Opcodes in member_db: {len(all_opcodes_in_db)}")
    print(f"Unique Opcodes in covered cards: {len(covered_opcodes)}")
    
    # Identify opcodes present in DB but not covered
    missing = all_opcodes_in_db - covered_opcodes
    print(f"Missing from tests: {sorted(list(missing))}")

if __name__ == "__main__":
    analyze_opcodes()
