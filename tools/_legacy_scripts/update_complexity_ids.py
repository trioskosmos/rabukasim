import json


def update_markdown_with_ids(json_path, md_path):
    with open(json_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    # Create mapping of name -> card_no
    # Note: Some names might be duplicates, pick the first one or logic based on complexity if needed
    name_to_id = {}
    for card in cards.values():
        name = card.get("name")
        if name and name not in name_to_id:
            name_to_id[name] = card.get("card_no")

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines = []
    for line in lines:
        if "|" in line and "Card Name" in line:
            updated_lines.append(line.replace("Card Name", "Card ID"))
        elif "|" in line and not line.strip().startswith("|---"):
            # Table row
            parts = line.split("|")
            if len(parts) > 1:
                name = parts[1].strip()
                if name in name_to_id:
                    parts[1] = f" {name_to_id[name]} "
                    updated_lines.append("|".join(parts))
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    with open(md_path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)


if __name__ == "__main__":
    update_markdown_with_ids("data/cards.json", "docs/card_complexity_tiers.md")
