import json
import os

DATA_FILE = 'data/consolidated_abilities.json'

def audit():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    target_ops = [
        'PLAY_MEMBER_FROM_DISCARD', 
        'RECOVER_LIVE', 
        'RECOVER_MEMBER', 
        'SELECT_CARDS', 
        'MOVE_TO_DISCARD',
        'MOVE_TO_DECK',
        'ACTIVATE_MEMBER',
        'PLAY_MEMBER_FROM_HAND'
    ]

    missing = []
    for jp, entry in data.items():
        pseudo = entry.get('pseudocode', '')
        if 'まで' in jp:
            lines = pseudo.split('\n')
            for line in lines:
                if any(op in line for op in target_ops) and '(Optional)' not in line:
                    missing.append((jp, line))
                    break

    print(f"Total entries with 'まで' and missing '(Optional)' on target effects: {len(missing)}")
    if missing:
        print("\nExamples:")
        for jp, line in missing[:10]:
            print(f"JP: {jp}")
            print(f"Pseudo Line: {line}")
            print("-" * 40)

if __name__ == '__main__':
    audit()
