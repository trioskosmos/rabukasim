import sys
import os

# --- PATH SETUP ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.game.data_loader import CardDataLoader


def diag(cid_or_no):
    loader = CardDataLoader("data/cards.json")
    m_db, l_db, e_db = loader.load()

    card = None
    cid = None

    # Try CID (int) first
    try:
        cid_int = int(cid_or_no)
        if cid_int in m_db:
            card, cid = m_db[cid_int], cid_int
        elif cid_int in l_db:
            card, cid = l_db[cid_int], cid_int
    except ValueError:
        pass

    # Try Card Number (string)
    if not card:
        for k, v in m_db.items():
            if v.card_no == cid_or_no:
                card, cid = v, k
                break
        if not card:
            for k, v in l_db.items():
                if v.card_no == cid_or_no:
                    card, cid = v, k
                    break

    if not card:
        print(f"Card {cid_or_no} not found.")
        return

    print(f"--- DIAGNOSTIC: {card.card_no} (CID: {cid}) ---")
    print(f"Name: {card.name}")
    print(f"Cost: {card.cost}")
    print(f"Abilities: {len(card.abilities)}")

    for i, ab in enumerate(card.abilities):
        print(f"\nAbility {i}:")
        print(f"  Trigger: {ab.trigger}")
        print(f"  Once per turn: {getattr(ab, 'is_once_per_turn', False)}")

        print(f"  Costs: {len(ab.costs)}")
        for c in ab.costs:
            print(f"    - Type: {c.cost_type}, Value: {c.value}, Optional: {getattr(c, 'is_optional', False)}")

        print(f"  Conditions: {len(ab.conditions)}")
        for cond in ab.conditions:
            print(f"    - Type: {cond.condition_type}, Value: {cond.value}, Attr: {cond.attr}, Params: {cond.params}")

        print(f"  Bytecode: {ab.bytecode}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/diag_card.py [CID or CardNo]")
    else:
        diag(sys.argv[1])
