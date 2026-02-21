import json
import os

import requests

REPLAY_FILE = "replays/game_14.json"
DATA_FILE = "data/cards.json"
BASE_URL = "https://llofficial-cardgame.com"


def main():
    print(f"Reading replay from {REPLAY_FILE}...")
    try:
        with open(REPLAY_FILE, "r", encoding="utf-8") as f:
            replay = json.load(f)
    except Exception as e:
        print(f"Failed to read replay: {e}")
        return

    # Extract unique img paths from states
    needed_imgs = set()

    def extract_imgs(obj):
        if isinstance(obj, dict):
            if "img" in obj and obj["img"]:
                needed_imgs.add(obj["img"])
            for k, v in obj.items():
                extract_imgs(v)
        elif isinstance(obj, list):
            for item in obj:
                extract_imgs(item)

    # Process states
    states = replay.get("states", [])
    print(f"Scanning {len(states)} frames...")
    extract_imgs(states)

    print(f"Found {len(needed_imgs)} unique images required for this replay.")

    # Load cards.json to resolve URLs
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        card_db = json.load(f)

    # Create mapping: relative_path -> full_url
    # cards.json key -> card -> img (full url)
    # But needed_imgs are "cards/..." (relative)
    # We need to find which full URL corresponds to each relative path
    # Or just construct it?

    # Strategy: iterate card_db, check if its relative path matches one of needed_imgs

    url_map = {}
    for cid, card in card_db.items():
        img_url = card.get("img", "")
        if not img_url:
            continue

        # transform full url to relative path to match needed_imgs
        # replay uses "cards/PLSD01/..."
        # full url "https://.../cardlist/PLSD01/..."
        if "/cardlist/" in img_url:
            rel = "cards/" + img_url.split("/cardlist/")[-1]
            if rel in needed_imgs:
                url_map[rel] = img_url

    # Check if we found URLs for all needed images
    missing_urls = needed_imgs - set(url_map.keys())
    if missing_urls:
        print(f"Warning: Could not find URLs for {len(missing_urls)} images: {list(missing_urls)[:3]}...")

    # Download
    print("Starting download...")
    count = 0
    headers = {"User-Agent": "Mozilla/5.0"}

    for rel_path, url in url_map.items():
        # Target: "web_ui/" + rel_path
        # rel_path is "cards/..."

        # wait, if rel_path starts with "cards/", and we map it to "cardlist/"
        # Replay uses "cards/..."

        # Correction: `download_cards.py` logic
        target_path = f"web_ui/{rel_path}"

        # But `game_board.html` expects `/img/cards/...`?
        # If server maps `/img` -> `web_ui`, then `/img/cards/...` -> `web_ui/cards/...`.
        # Check if `cards` folder is in `web_ui` root?
        # Yes.

        # BUT... `rel_path` from replay is `cards/BP02/...`.
        # So `web_ui/cards/BP02/...` is correct.

        if os.path.exists(target_path):
            continue

        print(f"Downloading {rel_path}...")
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "wb") as f:
                    f.write(r.content)
                count += 1
            else:
                print(f"Failed {r.status_code}: {url}")
        except Exception as e:
            print(f"Error {url}: {e}")

    print(f"Done! Downloaded {count} images.")


if __name__ == "__main__":
    main()
