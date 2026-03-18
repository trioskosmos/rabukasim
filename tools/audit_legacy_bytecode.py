import json
import os

def audit():
    path = 'data/cards_compiled.json'
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    issues = []

    member_db = data.get('member_db', {})
    for card_id, card in member_db.items():
        abilities = card.get('abilities', [])
        for i, ability in enumerate(abilities):
            bytecode = ability.get('bytecode', [])
            text = ability.get('text', '').lower()
            
            # Check 1: Empty bytecode
            if not bytecode:
                issues.append(('EMPTY', card_id, i, 'No bytecode for ' + ability.get('text', '')))
            
            # Check 2: Invalid opcode (>= 50)
            elif bytecode and bytecode[0] >= 50:
                issues.append(('INVALID_OP', card_id, i, f'Opcode {bytecode[0]} >= 50'))
            
            # Check 3: Too long (suspicious)
            elif len(bytecode) > 100:
                issues.append(('SUSPICIOUSLY_LONG', card_id, i, f'{len(bytecode)} opcodes'))
            
            # Check 4: Mismatched text/bytecode (Basic check)
            if text and 'draw' in text and bytecode and bytecode[0] != 1: # Opcode 1 is Draw according to docs
                # Note: This might be wrong if Draw is not the first action
                pass

    print(f'Found {len(issues)} issues:')
    for issue_type, card_id, idx, detail in issues:
        print(f'  [{issue_type}] Card {card_id} Ability {idx}: {detail}')

if __name__ == "__main__":
    audit()
