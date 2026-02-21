import os
import re

FILE_PATH = r"docs/missingpng.txt"


def list_all_pngs():
    if not os.path.exists(FILE_PATH):
        print(f"Error: {FILE_PATH} not found.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all strings ending in .png that are in a src attribute
    png_regex = re.compile(r'src="([^"]+\.png)"')
    matches = png_regex.findall(content)

    unique_pngs = sorted(list(set(matches)))

    print(f"Found {len(unique_pngs)} unique PNG URLs:")
    for png in unique_pngs:
        print(png)


if __name__ == "__main__":
    list_all_pngs()
