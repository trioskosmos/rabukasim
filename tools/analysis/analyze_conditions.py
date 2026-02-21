import os
import sys

sys.path.append(os.getcwd())

import json
from collections import Counter

from engine.models.ability import ConditionType


def main():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        cards = json.load(f)
    with open("verified_card_pool.json", "r", encoding="utf-8") as f:
        pool = json.load(f)

    verified = set(pool["verified_abilities"] + pool["vanilla_members"] + pool["vanilla_lives"])

    unverified = []
    condition_counts = Counter()

    for cno, card in cards.get("member_db", {}).items():
        if cno in verified:
            continue

        abilities = card.get("abilities", [])
        if not abilities:
            continue

        # Check conditions of first ability
        ab = abilities[0]
        conds = ab.get("conditions", [])

        if not conds:
            # Should have been caught by batch 1/2? Maybe complex effect?
            continue

        for c in conds:
            # Compiled JSON uses 'type', model uses 'condition_type'
            ctype = c.get("condition_type")
            if ctype is None:
                ctype = c.get("type")

            try:
                cname = ConditionType(ctype).name
            except:
                cname = f"UNKNOWN_{ctype}"
            condition_counts[cname] += 1

    print("Most Common Conditions in Unverified Cards:")
    for cname, count in condition_counts.most_common(10):
        print(f"{cname}: {count}")


if __name__ == "__main__":
    main()
