"""Extract diverse ability examples for manual review."""

import json


def main():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    cards = list(data.values())

    # Sample different card types
    samples = []
    seen_patterns = set()

    for card in cards:
        ability = card.get("ability", "")
        if not ability or len(ability) < 10:
            continue

        # Simple pattern: first 50 chars
        pattern = ability[:50]
        if pattern in seen_patterns:
            continue

        seen_patterns.add(pattern)
        samples.append({"id": card.get("card_no", ""), "name": card.get("name", ""), "ability": ability})

        if len(samples) >= 50:
            break

    # Print samples
    for i, sample in enumerate(samples, 1):
        print(f"\n{'=' * 80}")
        print(f"[{i}] {sample['id']} - {sample['name']}")
        print(f"{'=' * 80}")
        print(sample["ability"])


if __name__ == "__main__":
    main()
