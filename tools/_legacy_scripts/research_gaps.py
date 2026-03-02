import json

GAP_OPCODES = [
    22,
    26,
    34,
    38,
    46,
    52,
    80,
    83,  # Effects
    202,
    207,
    210,
    211,
    216,
    217,
    221,
    222,
    228,
    229,
    233,  # Conditions
]


def find_best_candidates():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db = json.load(f)

    results = {}

    # Check if db is dict or list
    cards = db.values() if isinstance(db, dict) else db

    for op in GAP_OPCODES:
        candidates = []
        for card in cards:
            for ab_idx, ab in enumerate(card.get("abilities", [])):
                bytecode = ab.get("bytecode", [])
                if op in bytecode:
                    # Complexity score = length of bytecode
                    candidates.append(
                        {
                            "card_no": card["card_no"],
                            "card_id": card["card_id"],
                            "name": card["name"],
                            "ab_idx": ab_idx,
                            "bytecode_len": len(bytecode),
                            "instruction_count": len(ab.get("instructions", [])),
                        }
                    )

        if candidates:
            # Sort by bytecode length descending
            candidates.sort(key=lambda x: x["bytecode_len"], reverse=True)
            results[op] = candidates[0]
        else:
            results[op] = None

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    find_best_candidates()
