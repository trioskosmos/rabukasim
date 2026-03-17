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

    # Find any src=".../filename.png"
    # Capture the full path, filename, and try to find an alt attribute nearby
    img_regex = re.compile(r'src="([^"]+\/([^"\/]+\.png))"')
    src_matches = img_regex.findall(content)

    unique_icons = {}
    for full_path, filename in src_matches:
        if filename not in unique_icons:
            unique_icons[filename] = BASE_URL + full_path if full_path.startswith("/") else full_path

    print(f"Found {len(unique_icons)} unique PNGs in the HTML:")

    targets = {"center.png", "heart_00.png", "icon_b_all.png", "icon_draw.png", "icon_score.png", "live_success.png"}

    print("\n--- Target Matches ---")
    for filename, url in sorted(unique_icons.items()):
        if filename in targets:
            print(f"MATCH: {filename} -> {url}")

    print("\n--- All Filenames ---")
    for filename in sorted(unique_icons.keys())[:50]:  # Cap list for readability
        print(filename)
    if len(unique_icons) > 50:
        print("...")


if __name__ == "__main__":
    extract_icons()
