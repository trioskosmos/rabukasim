import json


def deep_search():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Search for any mention of Energy and Opponent in same ability
    found_both = []
    # 2. Search for common comparison phrases
    comparison_phrases = ["自分より多い", "自分より少ない", "同じか高い", "同じか低い", "差", "比較"]
    found_comparison = []

    for card_no, card in data.items():
        ability = card.get("ability", "")
        if "エナジー" in ability and "相手" in ability:
            found_both.append((card_no, ability))

        for phrase in comparison_phrases:
            if phrase in ability:
                found_comparison.append((card_no, phrase, ability))
                break

    print("--- BOTH (Energy & Opponent) ---")
    print(f"Found {len(found_both)} cards:")
    for card_no, ability in found_both:
        print(f"- {card_no}: {ability[:120]}...")

    print("\n--- COMPARISONS ---")
    print(f"Found {len(found_comparison)} cards:")
    for card_no, phrase, ability in found_comparison[:10]:  # Just first 10
        print(f"- {card_no} (found '{phrase}'): {ability[:120]}...")


if __name__ == "__main__":
    deep_search()
