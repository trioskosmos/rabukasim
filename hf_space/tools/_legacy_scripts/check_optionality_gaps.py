import json


def check_optionality():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        manual = json.load(f)

    optional_phrases = ["してもよい", "することができる", "してよい"]
    results = []

    for card_id, card_data in cards.items():
        ability_text = card_data.get("ability", "")
        if any(phrase in ability_text for phrase in optional_phrases):
            # Found an optional ability in Japanese
            manual_entry = manual.get(card_id)
            if manual_entry:
                pseudocode = manual_entry.get("pseudocode", "")
                has_optional_tag = "(Optional)" in pseudocode
                # Split ability text by newline to see if all parts are optional or just some
                results.append(
                    {
                        "id": card_id,
                        "ability": ability_text,
                        "pseudocode": pseudocode,
                        "has_optional_tag": has_optional_tag,
                    }
                )

    # Print results
    print(f"{'ID':<20} | {'Has (Optional) Tag':<20}")
    print("-" * 45)
    for res in results:
        print(f"{res['id']:<20} | {str(res['has_optional_tag']):<20}")

    # Save detailed report
    with open("reports/optionality_gap_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    check_optionality()
