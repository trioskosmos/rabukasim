import os
import re
import sys

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pr_server  # To use card_no_to_id mapping


def parse_deck_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to find card numbers in title attributes
    # Example: title="PL!N-sd1-023-SD : ミア・テイラー"
    # We want "PL!N-sd1-023-SD"

    # Also look for quantity in "card-controller" -> "num" span?
    # <span class="num">2</span>

    # Strategy: Find "card-view-item" images, extract title, then find the NEXT "num" span.
    # Actually, simpler Regex: title="([^"]+) : [^"]+"

    matches = re.finditer(r'title="([^"]+) : ([^"]+)"', content)

    deck_list = []

    # We need to find quantities.
    # The HTML structure is:
    # <img ... title="CODE : NAME" ...>
    # ...
    # <span class="num">Q</span>

    # Let's simple split by "card-item" divs
    items = content.split('class="card-item')

    print(f"Found {len(items) - 1} card entries.")

    final_deck_ids = []

    pr_server.build_card_no_mapping()

    for item in items[1:]:  # Skip preamble
        # Extract Code
        code_match = re.search(r'title="([^"]+) : ', item)
        if not code_match:
            continue
        code = code_match.group(1)

        # Extract Quantity
        qty_match = re.search(r'<span class="num">(\d+)</span>', item)
        qty = int(qty_match.group(1)) if qty_match else 1

        print(f"Found: {code} x{qty}")

        # Convert to ID
        if code in pr_server.card_no_to_id:
            cid = pr_server.card_no_to_id[code]
            final_deck_ids.extend([cid] * qty)
        else:
            print(f"WARNING: Card code {code} not found in DB.")

    print(f"Total parsed deck size: {len(final_deck_ids)}")
    return final_deck_ids


if __name__ == "__main__":
    ids = parse_deck_html("tests/decktest.txt")
    print(f"Deck IDs: {ids}")

    # Save to a clean ID list file
    with open("tests/deck_ids.json", "w") as f:
        import json

        json.dump(ids, f)
