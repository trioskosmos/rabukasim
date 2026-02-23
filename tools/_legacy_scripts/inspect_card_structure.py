import json
import sys

def inspect():
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    mdb = data.get('member_db', {})
    if not mdb:
        print("member_db missing")
        return

    first_id = next(iter(mdb))
    card = mdb[first_id]
    print(f"Card {first_id} keys: {list(card.keys())}")
    
    abilities = card.get('abilities', [])
    if abilities:
        print(f"Ability 0 keys: {list(abilities[0].keys())}")
        print(f"Ability 0: {abilities[0]}")

if __name__ == "__main__":
    inspect()
