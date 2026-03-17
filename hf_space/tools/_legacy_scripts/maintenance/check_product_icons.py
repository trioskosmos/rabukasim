import json
import os
import re
from collections import defaultdict

# Paths
CARDS_JSON_PATH = r"engine/data/cards.json"

# The missing icons we are looking for
TARGET_ICONS = {"center.png", "heart_00.png", "icon_b_all.png", "icon_draw.png", "icon_score.png", "live_success.png"}


def analyze_products():
    if not os.path.exists(CARDS_JSON_PATH):
        print(f"Error: {CARDS_JSON_PATH} not found.")
        return

    try:
        with open(CARDS_JSON_PATH, "r", encoding="utf-8") as f:
            cards = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    icon_regex = re.compile(r"\{\{(.*?)\}\}")

    # Map product -> set of icons found in that product
    product_icons = defaultdict(set)

    for card_id, card_data in cards.items():
        product = card_data.get("product", "Unknown Product")
        ability = card_data.get("ability", "")
        if not ability:
            continue

        matches = icon_regex.findall(ability)
        for match in matches:
            parts = match.split("|")
            potential_filename = parts[0].strip()

            if potential_filename.lower().endswith(".png"):
                product_icons[product].add(potential_filename)

    print(f"Analyzing {len(product_icons)} products for target icons: {TARGET_ICONS}")

    matches_all = []

    print("\n--- Summary Matrix ---")
    print(f"{'Product':<40} | {'Found':<5} | {'Icons Present'}")
    print("-" * 100)

    # Sort by number of target icons found
    sorted_products = sorted(product_icons.items(), key=lambda x: len(TARGET_ICONS.intersection(x[1])), reverse=True)

    for product, icons in sorted_products:
        present = TARGET_ICONS.intersection(icons)
        if present:
            present_str = ", ".join(sorted(present))
            print(f"{product:<40} | {len(present):<5} | {present_str}")

    print("\n--- Minimal Product Set Calculation ---")

    # Simple Greedy Approach for Set Cover
    needed = set(TARGET_ICONS)
    selected_products = []

    # While we still need icons
    while needed:
        best_product = None
        best_cover = set()

        # Find product that covers the most *remaining* needed icons
        for product, icons in product_icons.items():
            cover = needed.intersection(icons)
            if len(cover) > len(best_cover):
                best_cover = cover
                best_product = product

        if not best_product:
            print("Cannot cover all icons with available products!")
            print(f"Remaining missing: {needed}")
            break

        selected_products.append(best_product)
        needed -= best_cover
        print(f"Selected: {best_product:<30} (Covers: {', '.join(sorted(best_cover))})")

    print(f"\nMinimal Set ({len(selected_products)} Products):")
    for p in selected_products:
        print(f"- {p}")


if __name__ == "__main__":
    analyze_products()
