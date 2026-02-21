import json
from collections import Counter


def analyze_full_coverage():
    with open("docs/full_ability_coverage.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    cards = data.get("with_ability", [])

    all_effects = Counter()
    all_triggers = Counter()
    all_conditions = Counter()
    all_costs = Counter()

    for card in cards:
        p = card.get("parsed", {})
        for eff in p.get("effects", []):
            all_effects[eff] += 1
        for tri in p.get("triggers", []):
            all_triggers[tri] += 1
        for con in p.get("conditions", []):
            all_conditions[con] += 1
        for cos in p.get("costs", []):
            all_costs[cos] += 1

    print(f"Total cards with abilities: {len(cards)}")
    print(f"Unique effects ({len(all_effects)}):")
    for k, v in all_effects.most_common():
        print(f"  {k}: {v}")

    print(f"\nUnique triggers ({len(all_triggers)}):")
    for k, v in all_triggers.most_common():
        print(f"  {k}: {v}")

    print(f"\nUnique conditions ({len(all_conditions)}):")
    for k, v in all_conditions.most_common():
        print(f"  {k}: {v}")

    print(f"\nUnique costs ({len(all_costs)}):")
    for k, v in all_costs.most_common():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    analyze_full_coverage()
