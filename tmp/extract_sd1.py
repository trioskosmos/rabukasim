
import json

def search():
    try:
        with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return

    for c in data['member_db'].values():
        if c.get('card_no') == 'PL!S-sd1-009-SD':
            print(f"Card: {c['card_no']}")
            for i, ab in enumerate(c.get('abilities', [])):
                print(f"Ability {i}:")
                print(f"  Pseudocode: {ab.get('pseudocode')}")
                print(f"  Bytecode: {ab.get('bytecode')}")

if __name__ == "__main__":
    search()
