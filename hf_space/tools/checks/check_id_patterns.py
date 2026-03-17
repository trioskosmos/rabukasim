import json
import os
import re


def check_id_patterns():
    # Load all cards
    if not os.path.exists("data/cards.json"):
        print("data/cards.json not found")
        return

    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    # Current Regex logic: matches starts with PL! or LL-
    # We want to find IDs that DO NOT start with these
    regex = re.compile(r"^(PL!|LL-)")

    unmatched = []
    prefixes = set()

    for cid in cards.keys():
        if not regex.match(cid):
            unmatched.append(cid)
            # Extract prefix for summary (e.g. "PR-001" -> "PR-")
            parts = cid.split("-")
            if parts:
                prefixes.add(parts[0])

    print(f"Total Cards: {len(cards)}")
    print(f"Cards matching (PL!|LL-): {len(cards) - len(unmatched)}")
    print(f"Cards NOT matching: {len(unmatched)}")

    if unmatched:
        print("\nUnmatched Patterns Found:")
        print(f"Prefixes: {sorted(list(prefixes))}")
        print("\nFirst 10 Unmatched IDs:")
        for cid in unmatched[:10]:
            print(f" - {cid}")


if __name__ == "__main__":
    check_id_patterns()
