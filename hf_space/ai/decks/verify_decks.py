import re

with open(
    r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\ai\decks\groupwinnersraw.txt", "r", encoding="utf-8"
) as f:
    content = f.read()

# Split by deck headers
sections = re.split(r'<h1 class="parts-h1-2">', content)
deck_sections = sections[1:]

names = ["Aqours", "Nijigaku", "Liella", "Muse", "Hasunosora"]

for i, section in enumerate(deck_sections):
    if i >= len(names):
        break

    print(f"--- {names[i]} Cup ---")

    # Split section by category headers
    categories = re.split(r'<h2 class="parts-h2-3">', section)
    # categories[0] is intro
    # Then usually Live, Member, Energy

    cat_counts = {}

    for cat_chunk in categories[1:]:
        # Get category name from the beginning of chunk
        cat_match = re.match(r"([^<]+)</h2>", cat_chunk)
        if not cat_match:
            continue
        cat_name = cat_match.group(1).strip()

        # Find all cards in this category
        matches = re.findall(r'<span class="sheet"><span>×</span><span>(\d+)</span></span>', cat_chunk)
        total_count = sum(int(c) for c in matches)
        unique_types = len(matches)

        cat_counts[cat_name] = (total_count, unique_types)
        print(f"  {cat_name}: {total_count} cards ({unique_types} unique types)")

    # Totals
    total_cards = sum(count for count, _ in cat_counts.values())
    print(f"  Total: {total_cards} cards")
    print()
