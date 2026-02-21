import json


def main():
    json_path = "data/manual_pseudocode.json"
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards_db = json.load(f)

    with open(json_path, "r", encoding="utf-8") as f:
        pseudo_db = json.load(f)

    # Strict keywords only. "できる" is excluded.
    keywords = ["てもよい"]

    fixed_count = 0
    cards_fixed = []

    for cid, card in cards_db.items():
        original_text = card.get("original_text", "")
        if not original_text:
            original_text = card.get("ability", "")

        if any(k in original_text for k in keywords):
            card_no = card["card_no"]
            entry = pseudo_db.get(card_no)
            if not entry:
                continue

            p_code = entry.get("pseudocode", "")
            lines = p_code.split("\n")
            new_lines = []
            modified = False

            for line in lines:
                # Target COST lines that are not already Optional
                if line.startswith("COST:") and "(Optional)" not in line:
                    new_lines.append(line + " (Optional)")
                    modified = True
                else:
                    new_lines.append(line)

            if modified:
                entry["pseudocode"] = "\n".join(new_lines)
                fixed_count += 1
                cards_fixed.append(card_no)

    if fixed_count > 0:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(pseudo_db, f, indent=2, ensure_ascii=False)
        print(f"Successfully modified {fixed_count} cards in {json_path}")
        print("Sample fixed cards:", cards_fixed[:5])
    else:
        print("No matches requiring fixes found.")


if __name__ == "__main__":
    main()
