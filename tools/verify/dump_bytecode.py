
import json
import sys
import os

# Mocking the engine environment is hard, but we can read the compiled data
def inspect_card(target_no):
    path = "data/cards_compiled.json"
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        db = json.load(f)

    # Search in members
    card = None
    for cid, m in db["member_db"].items():
        if m["card_no"] == target_no:
            card = m
            break
    
    if not card:
        print(f"Card {target_no} not found.")
        return

    print(f"--- [ CARD: {card['card_no']} ({card['name']}) ] ---")
    for i, ab in enumerate(card["abilities"]):
        print(f"\nAbility {i} (Trigger: {ab['trigger']}):")
        bc = ab["bytecode"]
        print(f"Bytecode: {bc}")
        # Decode ops
        idx = 0
        while idx < len(bc):
            op = bc[idx]
            v = bc[idx+1] if idx+1 < len(bc) else "?"
            a = bc[idx+2] if idx+2 < len(bc) else "?"
            s = bc[idx+3] if idx+3 < len(bc) else "?"
            print(f"  {idx:02}: OP={op:3} V={v:3} A={a:3} S={s:3}")
            idx += 4

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "PL!-sd1-003-SD"
    inspect_card(target)
