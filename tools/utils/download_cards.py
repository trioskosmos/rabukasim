import json
import os
import time

import requests

# Ensure directory exists
BASE_URL = "https://loveca-solo.pages.dev"
DATA_FILE = "data/cards.json"


def download_file(url_path, local_path):
    if os.path.exists(local_path):
        return  # Skip existing

    # Create directory if needed
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    # Try different URL variations if needed
    full_url = f"{BASE_URL}/{url_path}"
    # The source sometimes uses /wordpress/wp-content... so we need to be careful
    # But cards.json usually has relative paths or full paths?
    # Let's check cards.json structure first.

    print(f"Downloading: {full_url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        r = requests.get(full_url, headers=headers)
        if r.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(r.content)
            # print(f"Saved to {local_path}")
        else:
            print(f"Failed: {r.status_code} - {url_path}")
            # Try WP content path logic if needed?
            # From previous sessions, images were at /wordpress/wp-content/images/cardlist/...
            # If path in json is "cards/...", we might need to map it.

            # Fallback for "cards/" paths -> "wordpress/wp-content/images/cardlist/..." ??
            # Let's inspect ONE fail first.
            if url_path.startswith("cards/"):
                # Construct legacy path
                # e.g. cards/BP01/PL!-bp1-001-N.png
                # Source might be: /wordpress/wp-content/images/cardlist/BP01/PL!-bp1-001-N.png
                parts = url_path.split("/")
                if len(parts) >= 2:
                    legacy_url = f"{BASE_URL}/wordpress/wp-content/images/cardlist/{parts[1]}/{parts[2]}"
                    print(f"Trying legacy: {legacy_url}")
                    r2 = requests.get(legacy_url, headers=headers)
                    if r2.status_code == 200:
                        with open(local_path, "wb") as f:
                            f.write(r2.content)
                        print(f"Saved (Legacy) to {local_path}")

    except Exception as e:
        print(f"Error downloading {url_path}: {e}")

    time.sleep(0.1)


def main():
    print("Loading cards.json...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Found {len(data)} cards.")

    count = 0
    downloaded = 0

    print(f"Checked {count} cards. Found {len(data)} total entries.")

    # Collect tasks
    tasks = []
    for cid, card in data.items():
        img_url = card.get("img")
        if not img_url:
            continue

        if "/cardlist/" in img_url:
            rel_path = img_url.split("/cardlist/")[-1]
            local_path = f"web_ui/cards/{rel_path}"

            if not os.path.exists(local_path):
                tasks.append((img_url, local_path))

    print(f"Found {len(tasks)} images to download.")

    # Parallel download
    import concurrent.futures

    downloaded = 0
    failed = 0

    def download_one(args):
        url, path = args
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    f.write(r.content)
                return True
            else:
                return False
        except Exception:
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_one, t): t for t in tasks}

        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            if future.result():
                downloaded += 1
            else:
                failed += 1

            if (i + 1) % 50 == 0:
                print(f"Progress: {i + 1}/{len(tasks)} (Downloaded: {downloaded}, Failed: {failed})")

    print(f"Complete! Downloaded {downloaded}, Failed {failed}.")


if __name__ == "__main__":
    main()
