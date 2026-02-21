import json
import re
from collections import defaultdict


def check_style():
    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Auditing {len(data)} cards for style consistency...\n")

    issues = defaultdict(list)
    effect_types = defaultdict(int)
    non_canonical_effects = defaultdict(int)

    CANONICAL_MAP = {
        "ADD_HAND": "ADD_TO_HAND",
        "MOVE_HAND": "ADD_TO_HAND",
        "MOVE_TO_HAND": "ADD_TO_HAND",
        "TAP_PLAYER": "TAP_MEMBER",
        "TAP_SELF": "TAP_MEMBER",
        "CHARGE_SELF": "ENERGY_CHARGE",
        "CHARGE_ENERGY": "ENERGY_CHARGE",
        "MOVE_DISCARD": "MOVE_TO_DISCARD",
        "REMOVE_SELF": "MOVE_TO_DISCARD",
        "SWAP_SELF": "SWAP_ZONE",
        "DISCARD_HAND": "LOOK_AND_CHOOSE",  # Context dependent, but often used as cost which is fine
        "SELECT_LIMIT": "REDUCE_LIVE_SET_LIMIT",
        "POWER_UP": "BUFF_POWER",
        "REDUCE_SET_LIMIT": "REDUCE_LIVE_SET_LIMIT",
        "REDUCE_LIMIT": "REDUCE_LIVE_SET_LIMIT",
        "REDUCE_HEART": "REDUCE_HEART_REQ",
        "PREVENT_LIVE": "RESTRICTION",
        "MOVE_DECK": "MOVE_TO_DECK",
        "OPPONENT_CHOICE": "OPPONENT_CHOOSE",
        "SET_BASE_BLADES": "SET_BLADES",
        "GRANT_HEARTS": "ADD_HEARTS",
        "GRANT_HEART": "ADD_HEARTS",
        "SELECT_REVEALED": "LOOK_AND_CHOOSE",
        "LOOK_AND_CHOOSE_REVEALED": "LOOK_AND_CHOOSE",
        "CHANGE_BASE_HEART": "TRANSFORM_HEART",
        "SELECT_LIVE_CARD": "SELECT_LIVE",
        "POSITION_CHANGE": "MOVE_MEMBER",
        "INCREASE_HEART": "INCREASE_HEART_COST",
        "CHANGE_YELL_BLADE_COLOR": "TRANSFORM_COLOR",
    }

    for card_id, entry in data.items():
        if "pseudocode" not in entry:
            continue

        text = entry["pseudocode"]
        lines = text.split("\n")

        for line in lines:
            # Check spacing around keywords
            if re.search(r"(TRIGGER|COST|EFFECT|CONDITION):[^\s]", line):
                issues["Missing space after keyword"].append((card_id, line))

            # Extract effects
            if "EFFECT:" in line:
                eff_part = line.split("EFFECT:", 1)[1]
                # Split by semicolon, ignoring inside braces/parens is hard with regex,
                # but simple split usually works for effect names
                effects = re.findall(r"(\w+)\(", eff_part)
                for eff in effects:
                    effect_types[eff] += 1
                    if eff in CANONICAL_MAP:
                        non_canonical_effects[f"{eff} -> {CANONICAL_MAP[eff]}"] += 1
                        issues["Non-canonical Effect"].append((card_id, eff))

    # Report
    print("=== Non-Canonical Effects ===")
    for k, v in sorted(non_canonical_effects.items(), key=lambda x: x[1], reverse=True):
        print(f"{k}: {v}")

    print("\n=== Spacing Issues ===")
    print(f"Missing space after keyword: {len(issues['Missing space after keyword'])}")

    print("\n=== Top 20 Effect Types ===")
    for k, v in sorted(effect_types.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"{k}: {v}")


if __name__ == "__main__":
    check_style()
