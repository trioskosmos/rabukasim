import json


def analyze_nijigaku_distribution():
    with open("c:/Users/trios/.gemini/antigravity/scratch/loveca-copy/data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        cards = list(data.values())
    else:
        cards = data

    # Variants of Nijigasaki names in the data
    nijigaku_keywords = ["虹ヶ咲", "Nijigasaki", "虹学"]

    nijigaku_cards = []
    distribution = {"Member": 0, "Live": 0, "Energy": 0, "Total": 0}

    for card in cards:
        if not isinstance(card, dict):
            continue

        series = card.get("series", "")
        group = card.get("group", "")
        name = card.get("name", "")

        # Check series, group, or name (songs often have the group name in metadata)
        is_nijigaku = any(kw in series or kw in group or kw in name for kw in nijigaku_keywords)

        # Fallback: check rare_list names or other metadata if needed, but usually series is key
        if is_nijigaku:
            distribution["Total"] += 1
            ctype = card.get("type", "Unknown")
            if "メンバー" in ctype or "Member" in ctype:
                distribution["Member"] += 1
            elif "ライブ" in ctype or "Live" in ctype:
                distribution["Live"] += 1
            elif "エネルギー" in ctype or "Energy" in ctype:
                distribution["Energy"] += 1

            nijigaku_cards.append(card)

    print("=== Nijigaku Card Distribution Analysis ===\n")
    print(f"Total Nijigaku Cards: {distribution['Total']}")
    print(f"  - Members: {distribution['Member']}")
    print(f"  - Songs/Lives: {distribution['Live']}")
    print(f"  - Energy Cards: {distribution['Energy']}")
    print("\nSample Members:")
    unique_members = sorted(
        list(
            set(
                [
                    c.get("name")
                    for c in nijigaku_cards
                    if "メンバー" in c.get("type", "") or "Member" in c.get("type", "")
                ]
            )
        )
    )
    print(f"Unique Characters Found ({len(unique_members)}): {', '.join(unique_members[:13])}...")


if __name__ == "__main__":
    analyze_nijigaku_distribution()
