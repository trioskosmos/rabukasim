import json


def audit_nijigasaki():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        manual = json.load(f)

    batch_prefixes = ["PL!N-sd1", "PL!N-bp1"]
    audit_list = []

    for card_no, card_data in cards.items():
        if any(card_no.startswith(p) for p in batch_prefixes):
            manual_entry = manual.get(card_no, {})
            # Ability text can be in "ability" or "original_text" or "text"
            text = card_data.get("ability") or card_data.get("original_text") or card_data.get("text")
            audit_list.append(
                {
                    "card_no": card_no,
                    "name": card_data.get("name"),
                    "ability_text": text,
                    "current_pseudocode": manual_entry.get("pseudocode", card_data.get("pseudocode", "HEURISTIC_ONLY")),
                }
            )

    with open("nijigasaki_audit_source.json", "w", encoding="utf-8") as f:
        json.dump(audit_list, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    audit_nijigasaki()
