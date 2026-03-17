"""
Fix cards with "draw X, discard Y" pattern that were incorrectly compiled.

These cards have:
- DRAW effect with wrong params (from: discard)
- SWAP_CARDS effect instead of DISCARD_TO_ZONE
- DISCARD_HAND as cost instead of effect
"""

import json
import re

CARDS_PATH = "engine/data/cards_compiled.json"


def fix_draw_discard_cards():
    with open(CARDS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Pattern: カードをX枚引き、手札をY枚控え室に置く
    pattern = re.compile(r"カードを(\d+)枚引き、手札を(\d+)枚控え室に置く")

    fixed_count = 0
    fixed_cards = []

    # Iterate over member_db
    member_db = data.get("member_db", {})
    for card_id, card in member_db.items():
        if "abilities" not in card:
            continue

        for ability in card["abilities"]:
            raw_text = ability.get("raw_text", "")
            match = pattern.search(raw_text)

            if not match:
                continue

            draw_count = int(match.group(1))
            discard_count = int(match.group(2))

            # Check if this ability has the bug:
            # - Effect type 0 (DRAW) with wrong params
            # - Effect type 11 (SWAP_CARDS) instead of proper discard
            # - Cost type 3 (DISCARD_HAND) that should be an effect

            effects = ability.get("effects", [])
            costs = ability.get("costs", [])

            needs_fix = False

            # Check for DRAW with wrong params
            for eff in effects:
                if eff.get("effect_type") == 0:
                    params = eff.get("params", {})
                    if params.get("from") == "discard":
                        needs_fix = True
                        break
                if eff.get("effect_type") == 11:  # SWAP_CARDS incorrectly used
                    needs_fix = True
                    break

            # Check for DISCARD_HAND cost that should be effect
            for cost in costs:
                if cost.get("type") == 3:  # DISCARD_HAND
                    needs_fix = True
                    break

            if not needs_fix:
                continue

            # Fix the ability
            print(f"Fixing card {card_id}: {card.get('name', 'Unknown')} ({card.get('card_no', '')})")
            print(f"  Raw: {raw_text}")
            print(f"  Draw {draw_count}, Discard {discard_count}")

            ability["effects"] = [
                {
                    "effect_type": 0,  # DRAW
                    "value": draw_count,
                    "target": 1,  # SELF
                    "params": {},
                    "is_optional": False,
                },
                {
                    "effect_type": 3,  # DISCARD_TO_ZONE
                    "value": discard_count,
                    "target": 1,  # SELF
                    "params": {"from": "hand", "to": "discard"},
                    "is_optional": False,
                },
            ]
            ability["costs"] = []

            fixed_count += 1
            fixed_cards.append(f"{card_id}: {card.get('name')} ({card.get('card_no')})")

    # Write back the entire structure
    with open(CARDS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nFixed {fixed_count} cards:")
    for c in fixed_cards:
        print(f"  - {c}")


if __name__ == "__main__":
    fix_draw_discard_cards()
