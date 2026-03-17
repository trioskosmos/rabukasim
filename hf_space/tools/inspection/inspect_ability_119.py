import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data_loader import CardDataLoader


def inspect():
    loader = CardDataLoader("data/cards.json")
    member_db, _, _ = loader.load()

    card = member_db[119]  # ID from previous log
    print(f"Card: {card.name}")
    print(f"Raw: {card.ability_text}")

    found_recover = False
    found_swap = False
    for i, ab in enumerate(card.abilities):
        print(f"\nAbility {i}:")
        print(f"  Trigger: {ab.trigger}")
        print("  Costs:")
        for c in ab.costs:
            print(f"    - CostType {c.type} val={c.value}")
        print("  Effects:")
        for e in ab.effects:
            print(f"    - EffectType {e.effect_type} val={e.value} target={e.target} params={e.params}")
            if e.effect_type == 5:  # RECOVER_LIVE
                found_recover = True
            if e.effect_type == 11:  # SWAP_CARDS
                found_swap = True

    if found_recover and not found_swap:
        print("PASS: Found RECOVER_LIVE and NO generic SWAP.")
    elif found_recover and found_swap:
        print("FAIL: Found Both RECOVER_LIVE and SWAP (Double Parsing).")
    elif not found_recover:
        print("FAIL: Did NOT find RECOVER_LIVE.")


if __name__ == "__main__":
    inspect()
