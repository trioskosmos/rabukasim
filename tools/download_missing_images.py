import os
import re

import requests

# GitHub Repository Info
REPO_OWNER = "wlt233"
REPO_NAME = "llocg_db"
BRANCH = "master"
BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/img/cards"


def get_repo_contents(path=""):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching {url}: {response.status_code}")
        return []


def download_file(raw_url, local_path):
    print(f"Downloading {raw_url} to {local_path}...")
    response = requests.get(raw_url)
    if response.status_code == 200:
        with open(local_path, "wb") as f:
            f.write(response.content)
        return True
    else:
        print(f"Failed to download {raw_url}: {response.status_code}")
        return False


def main():
    report_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\reports\image_alignment_analysis_utf8.txt"
    download_dir = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\frontend\img\downloaded_temp"
    os.makedirs(download_dir, exist_ok=True)

    # 1. Parse missing cards
    missing_nos = []
    with open(report_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        capture = False
        for line in lines:
            if "--- TRULY MISSING" in line:
                capture = True
                continue
            if capture and line.strip() and "ID:" in line:
                match = re.search(r"\(([^)]+)\)", line)
                if match:
                    missing_nos.append(match.group(1))

    print(f"Found {len(missing_nos)} missing card numbers.")

    # 2. Map prefixes to potential folders
    # Based on observation:
    # PL!HS-sd1 -> HSSD01
    # PL!S-sd1 -> SSD01
    # PR -> PR
    # pb1 -> PB1 (guessing)

    folders_to_scan = ["HSSD01", "SSD01", "PR", "PB01", "PB02", "SD01", "SD02", "SD03"]

    # Actually, let's just fetch the whole directory structure once
    cards_root = get_repo_contents("img/cards")
    available_folders = [item["name"] for item in cards_root if item["type"] == "dir"]
    print(f"Available folders on GitHub: {available_folders}")

    # 3. Create a map of card_no snippets to raw URLs
    url_map = {}  # card_no snippet -> raw_url
    for folder in available_folders:
        print(f"Scanning folder: {folder}...")
        contents = get_repo_contents(f"img/cards/{folder}")
        for item in contents:
            if item["type"] == "file":
                # Filenames often look like PL!-PR-001.png or 001.png
                filename = item["name"]
                name_without_ext = os.path.splitext(filename)[0]
                url_map[name_without_ext] = item["download_url"]
                # Also index by full path if needed
                url_map[f"{folder}/{name_without_ext}"] = item["download_url"]

    # 4. Try to match and download
    downloaded_count = 0
    for card_no in missing_nos:
        # Try exact match
        found_url = None

        # Clean card_no for matching (GitHub repo might use different hyphens or case)
        clean_no = card_no.replace("＋", "+")

        # Try common variants
        # 1. Exact match
        if card_no in url_map:
            found_url = url_map[card_no]
        elif clean_no in url_map:
            found_url = url_map[clean_no]
        # 2. Match the numeric part (e.g. PL!HS-sd1-001 -> 001 if in HSSD01)
        elif "-0" in card_no:
            suffix = card_no.split("-")[-1]
            # Try to find folder-prefixed matches
            if "HS-sd1" in card_no and f"HSSD01/{suffix}" in url_map:
                found_url = url_map[f"HSSD01/{suffix}"]
            elif "S-sd1" in card_no and f"SSD01/{suffix}" in url_map:
                found_url = url_map[f"SSD01/{suffix}"]
            elif "PB-pb" in card_no:  # Guessing
                folder_guess = card_no.split("-")[1].upper()  # pb1 -> PB1
                if f"{folder_guess}/{suffix}" in url_map:
                    found_url = url_map[f"{folder_guess}/{suffix}"]

        if found_url:
            safe_name = card_no.replace("!", "_").replace("+", "_") + ".png"  # Save as png first
            local_path = os.path.join(download_dir, safe_name)
            if download_file(found_url, local_path):
                downloaded_count += 1
        else:
            print(f"Could not find URL for {card_no}")

    print(f"\nFinished. Downloaded {downloaded_count} files.")


if __name__ == "__main__":
    main()
