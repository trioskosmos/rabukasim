import os
import re

FILE_PATH = r"docs/missingpng.txt"
BASE_URL = "https://llofficial-cardgame.com"


def extract_icons():
    if not os.path.exists(FILE_PATH):
        print(f"Error: {FILE_PATH} not found.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all /wordpress/wp-content/images/texticon/filename.png
    icon_regex = re.compile(r"/wordpress/wp-content/images/texticon/[a-zA-Z0-9_\-]+\.png")
    matches = icon_regex.findall(content)

    unique_icons = sorted(list(set(matches)))

    targets = {"center.png", "heart_00.png", "icon_b_all.png", "icon_draw.png", "icon_score.png", "live_success.png"}

    print(f"Total unique icons found in texticon path: {len(unique_icons)}")
    print("\n--- Available Target Icons ---")
    for icon in unique_icons:
        filename = os.path.basename(icon)
        if filename in targets:
            full_url = BASE_URL + icon
            print(f"MATCH: {filename} -> {full_url}")

    print("\n--- All Found Icons ---")
    for icon in unique_icons:
        print(os.path.basename(icon))


if __name__ == "__main__":
    extract_icons()
