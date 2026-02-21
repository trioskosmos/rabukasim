import json
import os


def inspect_card(card_no):
    path = "data/cards_compiled.json"
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cards = [v for v in data["member_db"].values() if v.get("card_no") == card_no]
    if not cards:
        print(f"Card {card_no} not found")
        return

    card = cards[0]
    print(f"Card: {card['card_no']} ({card.get('name', 'N/A')})")
    print(f"Ability Count: {len(card['abilities'])}")
    for i, ab in enumerate(card["abilities"]):
        print(f"\nAbility {i}:")
        print(f"  Trigger: {ab['trigger']}")
        print(f"  Raw Text: {ab['raw_text']}")
        print(f"  Conditions: {len(ab['conditions'])}")
        for j, cond in enumerate(ab["conditions"]):
            print(f"    Condition {j}: Type {cond['type']}, Params {cond['params']}")
        print(f"  Effects: {len(ab['effects'])}")
        for j, eff in enumerate(ab["effects"]):
            print(f"    Effect {j}: Type {eff['effect_type']}, Value {eff['value']}, Params {eff['params']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        inspect_card(sys.argv[1])
    else:
        # Default interesting ones
        for c in ["PL!-pb1-008-R", "PL!SP-pb1-011-P＋", "PL!SP-bp4-017-N"]:
            inspect_card(c)
            print("=" * 40)
