import json


def find_missing_optional():
    with open("data/consolidated_abilities.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []

    # Common "may" patterns in Japanese card text
    MAY_PATTERNS = [
        "してもよい",
        "支払ってもよい",
        "置いてもよい",
        "加えてもよい",
        "登場させてもよい",
        "移動させてもよい",
        "アクティブにしてもよい",
    ]

    for jp_text, entry in data.items():
        pseudocode = entry.get("pseudocode", "")

        # Split JP text by common delimiters like ： or \n
        # Usually cost: effect
        parts = jp_text.split("：")
        if len(parts) < 2:
            continue

        effect_jp = parts[1]

        # Check if effect JP has "may"
        has_may_in_effect = any(p in effect_jp for p in MAY_PATTERNS)

        if not has_may_in_effect:
            continue

        # Check if pseudocode already marks effect as optional
        # We look at lines starting with EFFECT:
        lines = pseudocode.split("\n")
        effect_lines = [l for l in lines if l.startswith("EFFECT:")]

        if not effect_lines:
            continue

        # If any effect line has (Optional), it's probably fine
        is_already_optional = any("(Optional)" in l for l in effect_lines)

        if not is_already_optional:
            # Special case: LOOK_AND_CHOOSE often has it
            results.append({"jp": jp_text, "pseudocode": pseudocode, "cards": entry.get("cards", entry.get("ids", []))})

    print(f"Found {len(results)} potential missing optionals.")
    for r in results:
        print(f"Cards: {r['cards']}")
        print(f"JP snippet: {r['jp'][:100]}...")
        # print(f"Pseudocode: {r['pseudocode']}")
        print("-" * 20)


if __name__ == "__main__":
    find_missing_optional()
