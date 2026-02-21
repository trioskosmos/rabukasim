import json
import os
from collections import defaultdict
from datetime import datetime


def generate_report():
    # Load data
    try:
        with open("engine/data/cards.json", "r", encoding="utf-8") as f:
            cards_db = json.load(f)
            # Ensure it's a list for processing
            if isinstance(cards_db, dict):
                cards = []
                for k, v in cards_db.items():
                    # If v is the card object and k is the ID
                    v["id"] = k
                    cards.append(v)
            else:
                cards = cards_db
    except FileNotFoundError:
        print("Error: engine/data/cards.json not found")
        return

    try:
        with open("data/verified_card_pool.json", "r", encoding="utf-8") as f:
            verified_pool = json.load(f)
    except FileNotFoundError:
        print("Error: data/verified_card_pool.json not found")
        verified_pool = {"verified_abilities": [], "verified_lives": []}

    verified_ids = set(verified_pool.get("verified_abilities", []) + verified_pool.get("verified_lives", []))

    # Metrics
    total_cards = len(cards)
    verified_count = len(verified_ids)

    # By Type
    type_counts = defaultdict(lambda: {"total": 0, "verified": 0})
    for card in cards:
        ctype = card.get("type", "Unknown")
        type_counts[ctype]["total"] += 1
        if card.get("id") in verified_ids:
            type_counts[ctype]["verified"] += 1

    # Generate Markdown
    lines = []
    lines.append("# Master Verification Report")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Summary Table
    lines.append("## Summary")
    lines.append(f"- **Total Cards:** {total_cards}")
    lines.append(f"- **Verified:** {verified_count} ({verified_count / total_cards * 100:.1f}%)")
    lines.append("")

    lines.append("| Card Type | Total | Verified | Coverage |")
    lines.append("|---|---|---|---|")
    for ctype, stats in sorted(type_counts.items()):
        coverage = stats["verified"] / stats["total"] * 100 if stats["total"] > 0 else 0
        lines.append(f"| {ctype} | {stats['total']} | {stats['verified']} | {coverage:.1f}% |")

    lines.append("")

    # Detailed Breakdown (Optional - maybe top missing patterns?)
    # For now, just the high level metrics

    output_path = "docs/MASTER_REPORT.md"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    generate_report()
