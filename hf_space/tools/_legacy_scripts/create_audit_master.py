import collections
import json


def create_audit_master():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        # Load preserving order
        manual = json.load(f, object_pairs_hook=collections.OrderedDict)

    audit_data = []
    for card_no, manual_val in manual.items():
        card_info = cards.get(card_no, {})
        text = card_info.get("ability") or card_info.get("original_text") or card_info.get("text")
        audit_data.append(
            {
                "card_no": card_no,
                "name": card_info.get("name", "Unknown"),
                "original_text": text,
                "manual_pseudocode": manual_val.get("pseudocode"),
            }
        )

    with open("audit_master.json", "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False)
    print(f"Created audit_master.json with {len(audit_data)} entries.")


if __name__ == "__main__":
    create_audit_master()
