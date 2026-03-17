import os
import re
import time
import urllib.request

BASE_URL = "https://llofficial-cardgame.com"
TARGET_DIR = os.path.join("img", "texticon")
SOURCE_FILE = "temp_source_text.html"

if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)
    print(f"Created directory: {TARGET_DIR}")

if not os.path.exists(SOURCE_FILE):
    print(f"Error: {SOURCE_FILE} not found!")
    exit(1)

# Extract icons directly here
with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern for /wordpress/wp-content/images/texticon/...
matches = re.findall(r'src="(/wordpress/wp-content/images/texticon/[^"]+)"', content)
unique_icons = sorted(list(set(matches)))

print(f"Found {len(unique_icons)} icons to download.")

# Mimic a browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

for icon_path in unique_icons:
    # Construct full URL
    url = BASE_URL + icon_path

    # Extract filename
    filename = os.path.basename(icon_path)
    filepath = os.path.join(TARGET_DIR, filename)

    print(f"Downloading {url} to {filepath}...")

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            with open(filepath, "wb") as out_file:
                out_file.write(response.read())
        print("  Success")
    except Exception as e:
        print(f"  Failed: {e}")

    time.sleep(0.5)  # Be nice to the server

print("Download complete.")
