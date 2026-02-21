import json


def update_verified_pool():
    with open("batch3_parsing_check.json", "r", encoding="utf-8") as f:
        batch_cards = json.load(f)

    with open("verified_card_pool.json", "r", encoding="utf-8") as f:
        pool = json.load(f)

    verified_list = pool.get("verified_abilities", [])

    # We verified 41 cards. Let's get the card_no from batch_cards.
    # Note: Only those that were actually included in the test file.
    added_count = 0
    for card in batch_cards:
        if not card["abilities"]:
            continue

        cno = card["card_no"]
        if cno not in verified_list:
            verified_list.append(cno)
            added_count += 1

    verified_list.sort()
    pool["verified_abilities"] = verified_list

    with open("verified_card_pool.json", "w", encoding="utf-8") as f:
        json.dump(pool, f, indent=2, ensure_ascii=False)

    print(f"Added {added_count} cards to verified_card_pool.json")


if __name__ == "__main__":
    update_verified_pool()
