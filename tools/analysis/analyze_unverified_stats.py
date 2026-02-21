import os
import sys

sys.path.append(os.getcwd())

import json
from collections import Counter

from engine.models.ability import ConditionType, EffectType, TriggerType


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    cards = load_json("data/cards_compiled.json")
    pool = load_json("verified_card_pool.json")

    verified = set(pool["verified_abilities"] + pool["vanilla_members"] + pool["vanilla_lives"])

    cond_counts = Counter()
    effect_counts = Counter()
    trigger_counts = Counter()

    unverified_count = 0

    for cno, card in cards.get("member_db", {}).items():
        # Handle ID resolution
        real_cno = card.get("card_no")
        if not real_cno or real_cno in verified:
            continue

        abilities = card.get("abilities", [])
        if not abilities:
            continue

        unverified_count += 1

        # Analyze first ability for simplicity (primary blocker)
        ab = abilities[0]

        # Trigger
        trig = ab.get("trigger")
        try:
            tname = TriggerType(trig).name
        except:
            tname = str(trig)

        trigger_counts[tname] += 1

        # Conditions
        msg = "None"
        raw_conds = ab.get("conditions", [])
        if raw_conds:
            c_names = []
            for c in raw_conds:
                ctype = c.get("condition_type")  # or 'type'
                if ctype is None:
                    ctype = c.get("type")
                try:
                    cname = ConditionType(ctype).name
                except:
                    cname = f"UNK_{ctype}"
                c_names.append(cname)
            msg = "+".join(sorted(c_names))

        cond_counts[msg] += 1

        # Effects
        raw_effs = ab.get("effects", [])
        if raw_effs:
            e_names = []
            for e in raw_effs:
                etype = e.get("effect_type")
                try:
                    ename = EffectType(etype).name
                except:
                    ename = f"UNK_{etype}"
                e_names.append(ename)
            key = "+".join(sorted(e_names))
            effect_counts[key] += 1

    print(f"Total Unverified Ability Cards: {unverified_count}")
    print("\n--- Top Blocking Conditions ---")
    for k, v in cond_counts.most_common(10):
        print(f"{k}: {v}")

    print("\n--- Top Blocking Effects ---")
    for k, v in effect_counts.most_common(10):
        print(f"{k}: {v}")

    print("\n--- Top Triggers ---")
    for k, v in trigger_counts.most_common(5):
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
