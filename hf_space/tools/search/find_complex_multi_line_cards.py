import json


def find_complex_cards():
    with open("c:/Users/trios/.gemini/antigravity/scratch/loveca-copy/data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # If data is a dict (like what I saw in previous steps)
    if isinstance(data, dict):
        cards = list(data.values())
    else:
        cards = data

    complex_cards = []

    for card in cards:
        if not isinstance(card, dict):
            continue
        ability = card.get("ability", "")
        if not ability:
            continue

        # Split by newlines
        lines = ability.split("\n")
        if len(lines) <= 1:
            continue

        # Check if first line has trigger but others don't
        has_trigger_on_first = "{{" in lines[0]
        has_trigger_on_others = any("{{" in line for line in lines[1:] if line.strip())

        # If it has a continuation (line with text but no trigger)
        if has_trigger_on_first and not has_trigger_on_others:
            # Check for "Modal" keywords
            is_modal = "回答が" in ability or "場合" in ability

            complex_cards.append(
                {"card_no": card.get("card_no"), "name": card.get("name"), "ability": ability, "is_modal": is_modal}
            )

    print(f"Found {len(complex_cards)} potential multi-line continuation cards.\n")

    # Sort: Modal first
    complex_cards.sort(key=lambda x: x["is_modal"], reverse=True)

    for i, c in enumerate(complex_cards[:15]):
        modal_tag = "[MODAL] " if c["is_modal"] else ""
        print(f"{i + 1}. {modal_tag}{c['card_no']} - {c['name']}")
        print(f"   Text: {c['ability'].replace('\n', ' / ')}")
        print("-" * 40)


if __name__ == "__main__":
    find_complex_cards()
