
import json
with open('../data/cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    card = data['live_db'].get('519')
    if card:
        print(f"Card 519 found. Abilities: {len(card.get('abilities', []))}")
        for i, ab in enumerate(card.get('abilities', [])):
            print(f"Ability {i}: Trigger={ab.get('trigger')}, Bytecode={ab.get('bytecode')}")
    else:
        print("Card 519 not found in live_db.")
