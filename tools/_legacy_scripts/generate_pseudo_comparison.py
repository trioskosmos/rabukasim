import json
import os


def generate_comparison_report():
    # Load Master Data
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards_data = json.load(f)

    # Load Manual Pseudocode
    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        pseudo_data = json.load(f)

    report_path = "docs/archive/pseudocode_comparison_report.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Pseudocode vs Japanese Text Comparison Report\n\n")
        f.write(
            "This report lists every card's original Japanese ability text alongside its current pseudocode for manual verification.\n\n"
        )
        f.write("| Card ID | Japanese Ability Text | Pseudocode |\n")
        f.write("| --- | --- | --- |\n")

        for card_id, entry in pseudo_data.items():
            jp_text = "N/A"
            # Find the card in master data
            # cards_data is usually a list of cards or a dict of card lists
            # We need to find the card by ID
            if isinstance(cards_data, list):
                card = next((c for c in cards_data if c.get("id") == card_id), None)
            elif isinstance(cards_data, dict):
                # Check if it's card_id -> card dict
                card = cards_data.get(card_id)
                if not card:
                    # Maybe it's nested
                    for k, v in cards_data.items():
                        if isinstance(v, list):
                            card = next((c for c in v if c.get("id") == card_id), None)
                            if card:
                                break

            if card:
                # Some cards have multiple abilities, but manual_pseudocode is usually one block
                # We'll join them if there are multiple
                abilities = card.get("abilities", [])
                if abilities:
                    jp_text = "<br>---<br>".join([a.get("text", "").replace("\n", "<br>") for a in abilities])
                elif card.get("ability"):
                    jp_text = card.get("ability").replace("\n", "<br>")
                elif card.get("ability_text"):
                    jp_text = card.get("ability_text").replace("\n", "<br>")
                elif card.get("original_text"):
                    jp_text = card.get("original_text").replace("\n", "<br>")

            pseudo = entry.get("pseudocode", "").replace("\n", "<br>")
            f.write(f"| {card_id} | {jp_text} | {pseudo} |\n")

    print(f"Report generated: {report_path}")


if __name__ == "__main__":
    generate_comparison_report()
