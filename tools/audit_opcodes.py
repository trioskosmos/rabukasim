import json
from pathlib import Path
from collections import Counter

def audit_all_opcodes():
    path = Path('data/cards_compiled.json')
    if not path.exists():
        print("Compiled cards not found.")
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Opcode names for reporting
    with open('data/metadata.json', 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    OPCODE_NAMES = {v: k for k, v in metadata['opcodes'].items()}


    counts = Counter()
    card_samples = {}

    for card_id, card in data.get('member_db', {}).items():
        card_no = card.get('card_no', card_id)
        for ab in card.get('abilities', []):
            bc = ab.get('bytecode', [])
            for i in range(0, len(bc), 4):
                op = bc[i]
                counts[op] += 1
                if op not in card_samples:
                    card_samples[op] = []
                if card_no not in card_samples[op]:
                    card_samples[op].append(card_no)

    print(f"{'OP':<4} {'NAME':<25} {'COUNT':<5} {'SAMPLE'}")
    print("-" * 60)
    for op in sorted(counts.keys()):
        name = OPCODE_NAMES.get(op, f"UNKNOWN({op})")
        sample = ", ".join(card_samples.get(op, [])[:3])
        print(f"{op:<4} {name:<25} {counts[op]:<5} {sample}")

if __name__ == "__main__":
    audit_all_opcodes()
