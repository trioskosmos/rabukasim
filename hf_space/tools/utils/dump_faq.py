import json


def main():
    cards_path = "data/cards.json"
    with open(cards_path, encoding="utf-8") as f:
        cards = json.load(f)

    target_id = "PL!N-bp1-002-R＋"

    # Check if ID exists directly or via iteration
    card = cards.get(target_id)
    if not card:
        # Search values
        for k, v in cards.items():
            if v.get("card_no") == target_id:
                card = v
                break

    if not card:
        print(f"Card {target_id} not found.")
        return

    print(f"Found card: {card.get('name')}")
    faq = card.get("faq", [])

    with open("faq_dump.md", "w", encoding="utf-8") as f:
        f.write(f"# FAQ for {target_id}\n\n")
        for item in faq:
            f.write(f"## {item.get('title')}\n")
            f.write(f"**Q:** {item.get('question')}\n\n")
            f.write(f"**A:** {item.get('answer')}\n\n")

    print("FAQ dumped to faq_dump.md")


if __name__ == "__main__":
    main()
