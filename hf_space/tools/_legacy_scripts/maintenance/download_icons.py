import os

import requests

# Base URL for the icons
BASE_URL = "https://llofficial-cardgame.com/wordpress/wp-content/images/texticon/"

# List of missing icons
MISSING_ICONS = ["center.png", "heart_00.png", "icon_b_all.png", "icon_draw.png", "icon_score.png", "live_success.png"]

# Target directory
TARGET_DIR = r"frontend/web_ui/img/texticon"


def download_icons():
    # Ensure target directory exists
    if not os.path.exists(TARGET_DIR):
        print(f"Creating directory: {TARGET_DIR}")
        os.makedirs(TARGET_DIR, exist_ok=True)

    for icon in MISSING_ICONS:
        url = BASE_URL + icon
        filename = os.path.join(TARGET_DIR, icon)

        print(f"Downloading {url} ...")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"Successfully saved to {filename}")
            else:
                print(f"Failed to download {icon}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error downloading {icon}: {e}")


if __name__ == "__main__":
    download_icons()
