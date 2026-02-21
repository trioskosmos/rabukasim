import json

CARDS_PATH = "engine/data/cards.json"
POOL_PATH = "data/verified_card_pool.json"


def list_failures():
    with open(CARDS_PATH, "r", encoding="utf-8") as f:
        cards_db = json.load(f)

    with open(POOL_PATH, "r", encoding="utf-8") as f:
        pool_data = json.load(f)

    verified = set(pool_data.get("verified_abilities", []) + pool_data.get("verified_lives", []))

    failures = []
    for cid, card in cards_db.items():
        if cid not in verified:
            failures.append(card)

    print(f"Found {len(failures)} unverified cards.")

    # Group by Reason (rough heuristic)
    # Check if compiled?
    try:
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            compiled = json.load(f)
            # Flatten compiled
            compiled_ids = set()
            for k in compiled.get("member_db", {}):
                compiled_ids.add(k)
            for k in compiled.get("live_db", {}):
                compiled_ids.add(k)
            for k in compiled.get("energy_db", {}):
                compiled_ids.add(k)
    except:
        compiled_ids = set()

    types = {}
    for card in failures:
        ctype = card.get("type", "Unknown")
        types[ctype] = types.get(ctype, 0) + 1

    print("\nBreakdown by Type:")
    for t, c in types.items():
        print(f"  {t}: {c}")

    print("\nSample Failures:")
    for card in failures[:5]:
        print(f"- {card.get('card_no')} ({card.get('name')})")

    # Check if they are in compiled DB
    missing_compiled = [
        c.get("card_no") for c in failures if c.get("id") not in compiled_ids and c.get("card_no") not in compiled_ids
    ]
    # Note: compiled keys are ints usually, cards.json keys are IDs.
    # We need robust check.

    pass


if __name__ == "__main__":
    list_failures()
