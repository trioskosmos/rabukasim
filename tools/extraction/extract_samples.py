"""
Extract diverse card ability samples to file for manual review.
Handles Unicode properly and samples across different characteristics.
"""

import json
from collections import defaultdict


def main():
    # Read cards
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    cards = list(data.values())

    # Filter to cards with abilities
    cards_with_abilities = [c for c in cards if c.get("ability", "")]

    # Stratified sampling strategy
    samples = []

    # 1. Sample by card type
    by_type = defaultdict(list)
    for card in cards_with_abilities:
        card_type = card.get("type", "Unknown")
        by_type[card_type].append(card)

    for card_type, type_cards in by_type.items():
        # Take 2 examples from each type
        for card in type_cards[:2]:
            samples.append(card)
            if len(samples) >= 40:
                break
        if len(samples) >= 40:
            break

    # 2. Add cards with long ability text (likely complex)
    complex_cards = sorted(cards_with_abilities, key=lambda c: len(c.get("ability", "")), reverse=True)[:10]
    samples.extend(complex_cards)

    # 3. Add cards with specific keywords (unusual mechanics)
    keywords = ["相手", "対戦相手", "選ぶ", "ターン終了時", "公開", "見る"]
    for keyword in keywords:
        for card in cards_with_abilities:
            if keyword in card.get("ability", ""):
                samples.append(card)
                if len(samples) >= 60:
                    break
        if len(samples) >= 60:
            break

    # Deduplicate
    seen_ids = set()
    unique_samples = []
    for card in samples:
        card_id = card.get("card_no", "")
        if card_id not in seen_ids:
            seen_ids.add(card_id)
            unique_samples.append(card)

    # Write to file with UTF-8 encoding
    with open("ability_samples_manual.txt", "w", encoding="utf-8") as out:
        out.write("ABILITY SAMPLES FOR MANUAL REVIEW\n")
        out.write(f"Total samples: {len(unique_samples)}\n")
        out.write(f"{'=' * 80}\n\n")

        for i, card in enumerate(unique_samples[:50], 1):
            out.write(f"\n{'=' * 80}\n")
            out.write(f"[{i}] {card.get('card_no', 'N/A')} - {card.get('name', 'Unknown')}\n")
            out.write(f"Type: {card.get('type', 'N/A')}\n")
            out.write(f"{'=' * 80}\n")
            out.write(f"{card.get('ability', 'No ability')}\n")

    print(f"Extracted {len(unique_samples[:50])} samples to ability_samples_manual.txt")


if __name__ == "__main__":
    main()
