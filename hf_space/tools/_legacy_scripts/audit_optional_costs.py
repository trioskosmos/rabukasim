import json


def main():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards_db = json.load(f)

    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        pseudo_db = json.load(f)

    print(f"Loaded {len(cards_db)} cards and {len(pseudo_db)} pseudocodes.")

    candidates = []

    keywords = ["てもよい", "してもよい", "できる", "払ってもよい", "捨ててもよい"]

    correct_count = 0
    missing_cost_line = 0

    for i, (cid, card) in enumerate(cards_db.items()):
        # Fallback to 'ability' if 'original_text' is missing (which is true for source cards.json)
        original_text = card.get("original_text", "")
        if not original_text:
            original_text = card.get("ability", "")

        if i < 5:
            print(f"DEBUG [{cid}]: {original_text[:50]}...")

        if any(k in original_text for k in keywords):
            # Check pseudocode
            entry = pseudo_db.get(card["card_no"])
            if not entry:
                continue

            p_code = entry.get("pseudocode", "")
            lines = p_code.split("\n")
            cost_line = next((l for l in lines if l.startswith("COST:")), None)

            if cost_line:
                if "(Optional)" not in cost_line:
                    candidates.append(
                        {
                            "id": cid,
                            "no": card["card_no"],
                            "name": card["name"],
                            "cost": cost_line,
                            "text": original_text,
                            "match": next(k for k in keywords if k in original_text),
                        }
                    )
                else:
                    correct_count += 1
            else:
                missing_cost_line += 1

    print(f"Stats: Correctly marked: {correct_count}, Missing COST line: {missing_cost_line}")
    print(f"Found {len(candidates)} candidates needing fixes. Writing to audit_results.utf8.txt...")

    with open("audit_results.utf8.txt", "w", encoding="utf-8") as f:
        for c in candidates:
            f.write(f"[{c['no']}] {c['name']} (Match: {c['match']})\n")
            f.write(f"  Text: {c['text'].replace('\n', '')[:60]}...\n")
            f.write(f"  Curr: {c['cost']}\n")
            f.write("-" * 20 + "\n")


if __name__ == "__main__":
    main()
