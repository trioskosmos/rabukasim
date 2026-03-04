
import json
with open('../data/cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    def find_card(obj, target_id):
        if isinstance(obj, dict):
            if obj.get('card_id') == target_id:
                return obj
            for v in obj.values():
                res = find_card(v, target_id)
                if res: return res
        elif isinstance(obj, list):
            for v in obj:
                res = find_card(v, target_id)
                if res: return res
        return None

    card = find_card(data, 519)
    if card:
        print(f"Hearts: {card.get('hearts')}")
        print(f"Required Hearts: {card.get('required_hearts')}")
        print(f"Abilities: {len(card.get('abilities', []))}")
        for i, ab in enumerate(card.get('abilities', [])):
            if ab.get('trigger') == 6: # Constant
                print(f"Ability {i} Bytecode: {ab.get('bytecode')}")
    else:
        print("Card 519 not found.")
