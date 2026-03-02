import json

GAP_OPCODES = [22, 26, 34, 38, 46, 52, 80, 83]
GAP_CONDITIONS = [202, 207, 210, 211, 216, 217, 221, 222, 228, 229, 233]


def find_gaps():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db = json.load(f)

    cards = db.values() if isinstance(db, dict) else db

    results = {}

    for op in GAP_OPCODES + GAP_CONDITIONS:
        candidates = []
        for card in cards:
            for ab_idx, ab in enumerate(card.get("abilities", [])):
                bytecode = ab.get("bytecode", [])
                if op in bytecode:
                    candidates.append(
                        {
                            "card_no": card["card_no"],
                            "name": card["name"],
                            "ab_idx": ab_idx,
                            "bytecode": bytecode,
                            "text": ab.get("raw_text", ""),
                        }
                    )

        if candidates:
            # Sort by bytecode length to find "most complex"
            candidates.sort(key=lambda x: len(x["bytecode"]), reverse=True)
            results[op] = candidates[:3]  # Top 3 candidates
        else:
            results[op] = []

    with open("reports/gap_candidates.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    find_gaps()
