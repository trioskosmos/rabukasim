import json
import os
import re
from collections import Counter

# Paths
CARDS_JSON_PATH = r"engine/data/cards.json"
ICON_DIR = r"frontend/web_ui/img/texticon"


def check_icons():
    if not os.path.exists(CARDS_JSON_PATH):
        print(f"Error: {CARDS_JSON_PATH} not found.")
        return

    try:
        with open(CARDS_JSON_PATH, "r", encoding="utf-8") as f:
            cards = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    # Regex to find {{filename.png|...}} or {{filename.png}}
    # Captures the content inside {{...}}
    # patterns like: {{kidou.png|起動}} -> capture "kidou.png|起動"
    # then split by | and take the first part if it ends in .png
    icon_regex = re.compile(r"\{\{(.*?)\}\}")

    found_icons = Counter()

    for card_id, card_data in cards.items():
        ability = card_data.get("ability", "")
        if not ability:
            continue

        matches = icon_regex.findall(ability)
        for match in matches:
            # Handle "kidou.png|起動" or just "icon_blade.png" if that exists
            parts = match.split("|")
            potential_filename = parts[0].strip()

            if potential_filename.lower().endswith(".png"):
                found_icons[potential_filename] += 1

    print(f"Total unique PNG references found in abilities: {len(found_icons)}")
    print(f"Total total references: {sum(found_icons.values())}")

    missing_icons = []
    present_icons = []

    print("\n--- Checking File Existence ---")
    for icon_name in found_icons:
        icon_path = os.path.join(ICON_DIR, icon_name)
        if os.path.exists(icon_path):
            present_icons.append(icon_name)
        else:
            missing_icons.append(icon_name)

    print(f"Present: {len(present_icons)}")
    print(f"Missing: {len(missing_icons)}")

    if missing_icons:
        print("\n--- Missing Icons ---")
        for icon in sorted(missing_icons):
            print(f"- {icon} (Referenced {found_icons[icon]} times)")

    if present_icons:
        print("\n--- Present Icons (Top 10) ---")
        # Sort by frequency
        for icon in sorted(present_icons, key=lambda x: found_icons[x], reverse=True)[:10]:
            print(f"- {icon} (Referenced {found_icons[icon]} times)")


if __name__ == "__main__":
    check_icons()
