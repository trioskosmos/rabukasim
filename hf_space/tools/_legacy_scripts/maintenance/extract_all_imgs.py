import os
import re

FILE_PATH = r"docs/missingpng.txt"
BASE_URL = "https://llofficial-cardgame.com"


def extract_all_imgs():
    if not os.path.exists(FILE_PATH):
        print(f"Error: {FILE_PATH} not found.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all <img ... src="..." ... alt="..."> or variations
    # This regex is more robust to attribute order
    img_matches = re.finditer(r"<img[^>]+>", content)

    found_info = []

    for match in img_matches:
        img_tag = match.group(0)
        src_match = re.search(r'src="([^"]+)"', img_tag)
        alt_match = re.search(r'alt="([^"]*)"', img_tag)

        if src_match:
            src = src_match.group(1)
            alt = alt_match.group(1) if alt_match else ""
            found_info.append((src, alt))

    # Sort and filter unique
    unique_imgs = sorted(list(set(found_info)))

    target_alts = {
        "センター": "center.png",
        "ALLブレード": "icon_b_all.png",
        "ドロー": "icon_draw.png",
        "スコア": "icon_score.png",
        "ライブ成功時": "live_success.png",
        "SUCCESS": "live_success.png",
    }

    print("\n--- Potential Matches ---")
    for src, alt in unique_imgs:
        matched = False
        for target_alt, target_filename in target_alts.items():
            if target_alt in alt:
                full_url = BASE_URL + src if src.startswith("/") else src
                print(f"MATCH: {target_filename} (Alt: {alt}) -> {full_url}")
                matched = True

        # Also check for b_heart00 or similar in src
        if "heart" in src or "score" in src or "draw" in src:
            full_url = BASE_URL + src if src.startswith("/") else src
            print(f"POTENTIAL: {os.path.basename(src)} (Alt: {alt}) -> {full_url}")


if __name__ == "__main__":
    extract_all_imgs()
