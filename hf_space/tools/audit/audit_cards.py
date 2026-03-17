import json
import os


def audit_files():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cards_path = os.path.join(base_dir, "data", "cards.json")
    manual_path = os.path.join(base_dir, "data", "manual_pseudocode.json")
    output_path = os.path.join(base_dir, "tools", "audit_results.json")

    print(f"Scanning {cards_path}...")
    with open(cards_path, "r", encoding="utf-8") as f:
        cards_data = json.load(f)

    with open(manual_path, "r", encoding="utf-8") as f:
        manual_data = json.load(f)

    suspicious_entries = []

    # Audit cards.json
    for card_id, card in cards_data.items():
        if "pseudocode" in card:
            code = card["pseudocode"]
            if "-> CARD_DISCARD" in code:
                # Store details
                suspicious_entries.append(
                    {"id": card_id, "source": "cards.json", "code": code, "in_manual": card_id in manual_data}
                )

    # Audit manual_pseudocode.json
    for card_id, entry in manual_data.items():
        code = entry.get("pseudocode", "")
        if "-> CARD_DISCARD" in code:
            suspicious_entries.append(
                {"id": card_id, "source": "manual_pseudocode.json", "code": code, "in_manual": True}
            )

    print(f"Found {len(suspicious_entries)} suspicious entries. Writing to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(suspicious_entries, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    audit_files()
