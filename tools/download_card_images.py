"""
Download card images from GitHub repository and convert to WebP.

This script:
1. Fetches the list of card images from the GitHub repository (including subfolders)
2. Compares with existing images in frontend/img/cards_webp/
3. Downloads missing images
4. Converts PNG to WebP format
5. Saves to the appropriate folder

GitHub Repository: https://github.com/wlt233/llocg_db/tree/master/img/cards
"""

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Dict, List, Set, Tuple

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# GitHub API configuration
GITHUB_REPO = "wlt233/llocg_db"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}/contents"
RAW_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/master"

# Local paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "frontend", "img", "cards_webp")


def get_existing_images() -> Set[str]:
    """Get set of existing image names (without extension) in the output directory."""
    existing = set()
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            if f.endswith(".webp"):
                # Remove .webp extension
                existing.add(f[:-5])
    return existing


def fetch_github_contents(path: str = "img/cards") -> List[dict]:
    """Fetch contents from GitHub repository using API (recursive for subfolders)."""
    url = f"{GITHUB_API_BASE}/{path}"
    print(f"Fetching: {url}")

    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "LoveLive-Card-Downloader")

        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        return []
    except Exception as e:
        print(f"Error fetching GitHub contents: {e}")
        return []


def fetch_all_files(path: str = "img/cards", files_list: List[dict] = None) -> List[dict]:
    """Recursively fetch all files from GitHub repository."""
    if files_list is None:
        files_list = []

    contents = fetch_github_contents(path)

    for item in contents:
        if item["type"] == "file":
            files_list.append(item)
        elif item["type"] == "dir":
            # Recursively fetch subfolder contents
            fetch_all_files(item["path"], files_list)

    return files_list


def parse_filename(filename: str) -> Tuple[str, str]:
    """Parse filename to get base name and extension.

    Normalizes underscores to hyphens in the card number portion.
    Example: PL!N-bp1_034-PE2 -> PL!N-bp1-034-PE2
    """
    name, ext = os.path.splitext(filename)
    # Normalize underscores to hyphens in the card number
    # Pattern: prefix-set_number-suffix -> prefix-set-number-suffix
    # Example: PL!N-bp1_034-PE2 -> PL!N-bp1-034-PE2
    name = name.replace("_", "-")
    return name, ext.lower()


def convert_to_webp(input_path: str, output_path: str, quality: int = 85) -> bool:
    """Convert image to WebP format using PIL."""
    try:
        from PIL import Image

        with Image.open(input_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ("RGBA", "LA", "P"):
                # Keep transparency for WebP
                img.save(output_path, "webp", quality=quality, lossless=False)
            else:
                img = img.convert("RGB")
                img.save(output_path, "webp", quality=quality)

        return True
    except ImportError:
        print("Warning: PIL not installed. Cannot convert to WebP.")
        print("Install with: pip install Pillow")
        return False
    except Exception as e:
        print(f"Error converting to WebP: {e}")
        return False


def download_file(url: str, output_path: str) -> bool:
    """Download a file from URL."""
    try:
        urllib.request.urlretrieve(url, output_path)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def analyze_filename_format(files: List[dict]) -> Dict[str, int]:
    """Analyze filename formats in the repository."""
    formats = {}

    for f in files:
        name = f["name"]
        # Extract patterns
        if name.startswith("PL!"):
            prefix = "PL!"
        elif name.startswith("LL-"):
            prefix = "LL-"
        else:
            prefix = "other"

        ext = os.path.splitext(name)[1].lower()
        key = f"{prefix}_{ext}"
        formats[key] = formats.get(key, 0) + 1

    return formats


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Download card images from GitHub and convert to WebP")
    parser.add_argument("--dry-run", action="store_true", help="Only list missing files, don't download")
    parser.add_argument("--quality", type=int, default=85, help="WebP quality (default: 85)")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of downloads (0 = no limit)")
    parser.add_argument("--no-convert", action="store_true", help="Don't convert to WebP, keep original format")
    parser.add_argument("--analyze", action="store_true", help="Analyze filename formats")

    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get existing images
    existing = get_existing_images()
    print(f"Found {len(existing)} existing images in {OUTPUT_DIR}")

    # Fetch all files from GitHub (including subfolders)
    print("\nFetching all files from GitHub repository...")
    files = fetch_all_files("img/cards")

    if not files:
        print("No files found or error fetching from GitHub")
        return

    print(f"Found {len(files)} total files in GitHub repository")

    # Filter for image files
    image_files = [
        f for f in files if f["type"] == "file" and f["name"].lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]

    print(f"Found {len(image_files)} image files")

    # Analyze filename formats if requested
    if args.analyze:
        formats = analyze_filename_format(image_files)
        print("\nFilename format analysis:")
        for fmt, count in sorted(formats.items()):
            print(f"  {fmt}: {count}")
        print()

    # Find missing images
    missing = []
    for f in image_files:
        base_name, ext = parse_filename(f["name"])

        # Check if we already have this image (as webp)
        if base_name not in existing:
            # Get download URL
            download_url = f.get("download_url")
            if not download_url:
                # Construct download URL from path
                download_url = f"{RAW_BASE_URL}/{f['path']}"
            missing.append((base_name, ext, download_url))

    print(f"\nFound {len(missing)} missing images")

    if args.dry_run:
        print("\nMissing images (dry run):")
        for base_name, ext, url in missing[:100]:  # Show first 100
            print(f"  {base_name}{ext}")
        if len(missing) > 100:
            print(f"  ... and {len(missing) - 100} more")

        # Show sample URLs
        if missing:
            print("\nSample download URLs:")
            for base_name, ext, url in missing[:3]:
                print(f"  {base_name}: {url}")
        return

    if not missing:
        print("No missing images to download")
        return

    # Download and convert
    downloaded = 0
    failed = 0

    # Create temp directory for downloads
    temp_dir = os.path.join(PROJECT_ROOT, "temp_images")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        for i, (base_name, ext, url) in enumerate(missing):
            if args.limit > 0 and downloaded >= args.limit:
                print(f"\nReached download limit of {args.limit}")
                break

            print(f"[{i + 1}/{len(missing)}] Downloading {base_name}{ext}...", end=" ")

            # Download to temp file
            temp_path = os.path.join(temp_dir, f"{base_name}{ext}")

            if not download_file(url, temp_path):
                print("FAILED (download)")
                failed += 1
                continue

            # Convert to WebP
            if not args.no_convert:
                output_path = os.path.join(OUTPUT_DIR, f"{base_name}.webp")
                if convert_to_webp(temp_path, output_path, args.quality):
                    print("OK (converted to WebP)")
                    downloaded += 1
                    # Remove temp file
                    os.remove(temp_path)
                else:
                    print("FAILED (conversion)")
                    failed += 1
            else:
                # Just move to output directory
                output_path = os.path.join(OUTPUT_DIR, f"{base_name}{ext}")
                os.rename(temp_path, output_path)
                print("OK")
                downloaded += 1

    finally:
        # Clean up temp directory
        if os.path.exists(temp_dir):
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)

    print(f"\nDownloaded: {downloaded}")
    print(f"Failed: {failed}")
    print(f"Total images in folder: {len(get_existing_images())}")


if __name__ == "__main__":
    main()
