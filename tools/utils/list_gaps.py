def list_gaps():
    with open("docs/master_ability_report.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Split by card sections
    cards = content.split("### ")[1:]

    print(f"Found {len(cards)} cards in report.")

    gaps_found = 0
    for card in cards:
        lines = card.split("\n")
        title = lines[0].strip()

        gaps_line = next((l for l in lines if "**Gaps:**" in l), None)
        if gaps_line:
            gaps = gaps_line.split("**Gaps:**")[1].strip()
            if gaps and gaps != "None":
                print(f"{title}")
                print(f"  Gap: {gaps}")
                # Find text
                text_idx = next((i for i, l in enumerate(lines) if "**Text:**" in l), -1)
                if text_idx != -1:
                    print(f"  Text: {lines[text_idx + 2].strip()}")
                # Find parsed
                parsed_idx = next((i for i, l in enumerate(lines) if "**Parsed:**" in l), -1)
                if parsed_idx != -1:
                    print(f"  Parsed: {lines[parsed_idx].split('**Parsed:**')[1].strip()}")
                print("-" * 20)
                gaps_found += 1

    print(f"Total Gaps: {gaps_found}")


if __name__ == "__main__":
    list_gaps()
