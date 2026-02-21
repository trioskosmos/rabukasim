import json
from pathlib import Path

def analyze_impact():
    path = Path('data/cards_compiled.json')
    if not path.exists():
        print("Compiled cards not found.")
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    affected_count = 0
    total_lac = 0
    affected_ids = []

    for card_id, card in data.get('member_db', {}).items():
        abilities = card.get('abilities', [])
        for ab in abilities:
            bc = ab.get('bytecode', [])
            for i in range(0, len(bc), 4):
                if bc[i] == 41:  # O_LOOK_AND_CHOOSE
                    total_lac += 1
                    # A slot of 6 (CARD_HAND) for a LOOK_AND_CHOOSE effect
                    # that isn't explicitly sourcing from hand is the bug pattern.
                    # Since I've already fixed it, I'll count how many cards
                    # mention 'CARD_HAND' in the pseudocode's effect part.
                    pseudo = ab.get('pseudocode', '').upper()
                    if 'EFFECT:' in pseudo:
                        effect_part = pseudo.split('EFFECT:')[1]
                        if 'CARD_HAND' in effect_part or 'ADD_TO_HAND' in effect_part:
                            affected_count += 1
                            affected_ids.append(card.get('card_no', card_id))
                            break

    print(f"Total cards using LOOK_AND_CHOOSE: {total_lac}")
    print(f"Cards where EFFECT targets CARD_HAND: {affected_count}")
    print(f"Sample impacted card numbers: {', '.join(affected_ids[:10])}...")

if __name__ == "__main__":
    analyze_impact()
