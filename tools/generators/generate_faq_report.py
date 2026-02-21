import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from game.data_loader import CardDataLoader


def main():
    print("Loading Cards...")
    json_path = os.path.join("data", "cards.json")
    loader = CardDataLoader(json_path)
    members, lives, _ = loader.load()

    all_cards = list(members.values()) + list(lives.values())

    cards_with_faq = [c for c in all_cards if hasattr(c, "faq") and c.faq]
    cards_with_faq.sort(key=lambda x: x.card_no)

    print(f"Found {len(cards_with_faq)} cards with FAQs.")

    os.makedirs("docs", exist_ok=True)

    with open("docs/faq_report.md", "w", encoding="utf-8") as f:
        f.write("# Love Live! TCG - Known FAQs\n\n")
        f.write(f"**Total Cards with FAQs**: {len(cards_with_faq)}\n\n")
        f.write("---\n\n")

        for card in cards_with_faq:
            f.write(f"## {card.name} ({card.card_no})\n")

            for faq in card.faq:
                f.write(f"### {faq.title}\n")
                f.write(f"**Q**: {faq.question}\n\n")
                f.write(f"**A**: {faq.answer}\n\n")

                if faq.relation:
                    f.write("**Related Cards**:\n")
                    for rel in faq.relation:
                        f.write(f"- {rel.get('name', '')} ({rel.get('card_no', '')})\n")
                    f.write("\n")

            f.write("---\n\n")

    print("Report generated: docs/faq_report.md")


if __name__ == "__main__":
    main()
