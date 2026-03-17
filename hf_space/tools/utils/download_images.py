import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


def download_single_image(args):
    """Download a single image. Returns (success, card_id, message)"""
    card_id, img_url, local_path = args

    if os.path.exists(local_path):
        return (True, card_id, "already exists")

    # Ensure directory exists
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(img_url, timeout=30, headers=headers)
        if r.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(r.content)
            return (True, card_id, "downloaded")
        else:
            return (False, card_id, f"HTTP {r.status_code}")
    except Exception as e:
        return (False, card_id, str(e))


def download_images():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Total cards in database: {len(data)}")

    # Build list of images to download
    to_download = []
    for card_id, card in data.items():
        img_url = card.get("img")
        local_path = card.get("_img")

        if not img_url or not local_path:
            continue

        to_download.append((card_id, img_url, local_path))

    print(f"Total images to check: {len(to_download)}")

    # Check how many already exist
    already_exists = sum(1 for _, _, path in to_download if os.path.exists(path))
    print(f"Already downloaded: {already_exists}")
    print(f"Remaining to download: {len(to_download) - already_exists}")

    if already_exists == len(to_download):
        print("All images already downloaded!")
        return

    # Download with thread pool for speed
    success_count = 0
    fail_count = 0
    skip_count = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_single_image, args): args for args in to_download}

        for i, future in enumerate(as_completed(futures)):
            success, card_id, message = future.result()

            if message == "already exists":
                skip_count += 1
            elif success:
                success_count += 1
                print(f"[{i + 1}/{len(to_download)}] Downloaded: {card_id}")
            else:
                fail_count += 1
                print(f"[{i + 1}/{len(to_download)}] Failed: {card_id} - {message}")

            # Progress update every 100 images
            if (i + 1) % 100 == 0:
                print(
                    f"Progress: {i + 1}/{len(to_download)} ({success_count} new, {skip_count} skipped, {fail_count} failed)"
                )

    print("\n=== Download Complete ===")
    print(f"New downloads: {success_count}")
    print(f"Already existed: {skip_count}")
    print(f"Failed: {fail_count}")


if __name__ == "__main__":
    download_images()
