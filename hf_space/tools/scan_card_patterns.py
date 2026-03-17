import json
import re


def scan_cards():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    interesting_cards = []

    for cid, data in cards.items():
        ability = data.get("ability", "")
        if not ability:
            continue

        reasons = []

        # Newlines that don't start with bullets
        if "\\n" in ability:
            blocks = ability.split("\\n")
            for b in blocks[1:]:
                if b and not b.strip().startswith("・") and not b.strip().startswith("-"):
                    reasons.append("Newline without bullet")
                    break

        # Parentheses
        if "（" in ability or "(" in ability:
            reasons.append("Parentheses")

        # "選ぶ" variants
        if "選ぶ" in ability and "以下から" not in ability:
            reasons.append("Select without 'From following'")

        # "場合" at the start of a sentence
        if "。場合" in ability or ability.startswith("場合"):
            reasons.append("Sentence starts with 'Case'")

        # Multiple triggers
        if len(re.findall(r"\{\{.*?\}\}", ability)) > 1:
            reasons.append("Multiple Icons")

        if reasons:
            interesting_cards.append({"id": cid, "reasons": list(set(reasons)), "text": ability})

    # Group by combination of reasons
    groups = {}
    for c in interesting_cards:
        r_key = "|".join(sorted(c["reasons"]))
        if r_key not in groups:
            groups[r_key] = []
        groups[r_key].append(c)

    final_output = {
        "total": len(interesting_cards),
        "groups": {k: v[:10] for k, v in groups.items()},  # Take top 10 from each
    }

    with open("scan_results.json", "w", encoding="utf-8") as out:
        json.dump(final_output, out, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    scan_cards()
