import json
import sys


def check_card(cid):
    with open("engine/data/cards_compiled.json", "r") as f:
        data = json.load(f)

    card = data["member_db"].get(str(cid))
    if not card:
        # Check live_db too
        card = data.get("live_db", {}).get(str(cid))

    if not card:
        print(f"Card {cid} not found")
        return

    print(f"Card {cid}: {card['name']}")
    for i, ab in enumerate(card["abilities"]):
        print(f"Ability {i} Trigger: {ab['trigger']}: {ab['raw_text']}")
        for j, eff in enumerate(ab["effects"]):
            is_opt = eff.get("is_optional", False)
            print(f"  Effect {j}: {eff['effect_type']} (Val: {eff['value']}) Opt: {is_opt} Params: {eff.get('params')}")


if __name__ == "__main__":
    cid = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    check_card(cid)
