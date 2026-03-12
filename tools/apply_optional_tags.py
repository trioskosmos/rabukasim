import json
import os
import re

DATA_FILE = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\consolidated_abilities.json'

def update_abilities():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    count = 0
    # The key IS the JP text in consolidated_abilities.json
    for jp, entry in data.items():
        pseudo = entry.get('pseudocode', '')
        
        # Check if JP contains "まで" or "枚まで" or similar "up to" expressions
        # but Pseudo is missing (Optional)
        if 'まで' in jp and '(Optional)' not in pseudo:
            # List of opcodes that should be marked (Optional) if they are "up to X"
            target_ops = [
                'PLAY_MEMBER_FROM_DISCARD', 
                'RECOVER_LIVE', 
                'RECOVER_MEMBER', 
                'SELECT_CARDS', 
                'MOVE_TO_DISCARD',
                'MOVE_TO_DECK',
                'ACTIVATE_MEMBER'
            ]
            
            lines = pseudo.split('\n')
            new_lines = []
            modified = False
            for line in lines:
                if any(op in line for op in target_ops) and '(Optional)' not in line:
                    # Append (Optional) before the end of the effect or parameters
                    if '{' in line:
                        line = line.replace('{', '(Optional) {', 1)
                    elif '->' in line:
                        line = line.replace('->', '(Optional) ->', 1)
                    else:
                        line += ' (Optional)'
                    count += 1
                    modified = True
                new_lines.append(line)
            
            if modified:
                entry['pseudocode'] = '\n'.join(new_lines)

    print(f"Updated {count} pseudocode entries.")
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    update_abilities()
