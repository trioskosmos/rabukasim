import os
import re
from collections import Counter


def extract_deck_data(content, card_db):
    """
    Parses HTML content to extract card IDs and quantities.
    Returns (main_deck, energy_deck, type_counts, errors)
    """
    # HTML Structure:
    # title="PL!xxx-yyy-zzz : NAME" ... <span class="num">N</span>
    pattern = r'title="([^"]+?) :[^"]*"[^>]*>.*?class="num">(\d+)</span>'
    matches = re.findall(pattern, content, re.DOTALL)

    matches = re.findall(pattern, content, re.DOTALL)

    if not matches:
        # Fallback 1: Text format "4 x ID Name"
        # Regex: Start of line or space, (digits) x (ID), ignoring rest of line
        # We need to be careful about the ID format. It usually contains uppercase letters, numbers, -, !, +
        # Example: 4 x LL-bp3-001-R＋
        text_pattern_1 = r"(\d+)\s*[xX]\s*([A-Za-z0-9!+\-＋]+)"
        matches_1 = re.findall(text_pattern_1, content)

        if matches_1:
            # Swap to (ID, Qty) format to match HTML output
            matches = [(m[1], m[0]) for m in matches_1]
            print(f"Detected Text Format (Qty x ID): Found {len(matches)} entries.")
        else:
            # Fallback 2: Text format "ID x 4"
            # Include full-width plus '＋' in the character class
            text_pattern_2 = r"([A-Za-z0-9!+\-＋]+)\s*[xX]\s*(\d+)"
            matches_2 = re.findall(text_pattern_2, content)

            if matches_2:
                matches = matches_2
                print(f"Detected Text Format (ID x Qty): Found {len(matches)} entries.")

    if not matches:
        # Keep original fallback (just count titles) or fail
        pattern_title = r'title="((?:PL!|LL-E)[^"]+?) :'
        # ... logic ...
        return [], [], {}, ["No card ID + quantity pairs found."]

    main_deck = []
    energy_deck = []

    type_counts = {"Member": 0, "Live": 0, "Energy": 0, "Unknown": 0}

    errors = []

    for card_id, qty_str in matches:
        qty = int(qty_str)
        card_id = card_id.strip()

        # Determine Type
        cdata = card_db.get(card_id, {})
        ctype = cdata.get("type", "")

        if "メンバー" in ctype:
            type_counts["Member"] += qty
        elif "ライブ" in ctype:
            type_counts["Live"] += qty
        elif "エネルギー" in ctype:
            type_counts["Energy"] += qty
        else:
            type_counts["Unknown"] += qty

        for _ in range(qty):
            # Use card type to properly separate energy cards
            if "エネルギー" in ctype:
                energy_deck.append(card_id)
            else:
                main_deck.append(card_id)

    # Validation Rules
    main_counts = Counter(main_deck)
    energy_counts = Counter(energy_deck)
    all_counts = main_counts + energy_counts

    for cid, count in all_counts.items():
        if count > 4 and not cid.startswith("LL-E"):
            errors.append(f"Card limit exceeded: {cid} x{count} (Max 4)")

    return main_deck, energy_deck, type_counts, errors


def parse_and_validate_deck(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Load card DB
    card_db = {}
    try:
        import json

        with open("data/cards.json", "r", encoding="utf-8") as f:
            card_db = json.load(f)
    except Exception as e:
        print(f"Warning: Could not load cards.json: {e}")

    main_deck, energy_deck, type_counts, errors = extract_deck_data(content, card_db)

    if not main_deck and not energy_deck and errors:
        print(errors[0])
        return

    # Output Report
    with open("deck_report.txt", "w", encoding="utf-8") as f:
        f.write(f"=== Deck Verification Report for {os.path.basename(file_path)} ===\n")
        f.write(f"Total Cards: {len(main_deck) + len(energy_deck)}\n")
        f.write(
            f"Breakdown: Member: {type_counts['Member']} | Live: {type_counts['Live']} | Energy: {type_counts['Energy']}\n"
        )

        f.write(f"\nMain Deck: {len(main_deck)} cards\n")
        main_counts = Counter(main_deck)
        for cid, count in sorted(main_counts.items()):
            cname = card_db.get(cid, {}).get("name", "Unknown")
            f.write(f"  {cid}: x{count} ({cname})\n")

        f.write(f"\nEnergy Deck: {len(energy_deck)} cards\n")
        energy_counts = Counter(energy_deck)
        for cid, count in sorted(energy_counts.items()):
            cname = card_db.get(cid, {}).get("name", "Unknown")
            f.write(f"  {cid}: x{count} ({cname})\n")

        f.write("\n--- Validation Results ---\n")
        if not errors:
            f.write("VALID DECK (No copy limit violations)\n")
        else:
            f.write("DECK HAS ISSUES:\n")
            for e in errors:
                f.write(f"- {e}\n")

    print("Report written to deck_report.txt")
    print(f"Total: {len(main_deck)} Main + {len(energy_deck)} Energy")
    print(f"Types: Member {type_counts['Member']}, Live {type_counts['Live']}, Energy {type_counts['Energy']}")

    # Auto-upload to server if running
    try:
        import urllib.error
        import urllib.request

        server_url = "http://localhost:8000"

        # 1. Set Deck
        payload = {"player": 0, "deck": main_deck, "energy_deck": energy_deck}
        req = urllib.request.Request(
            f"{server_url}/api/set_deck",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as response:
            print("Successfully sent deck to server.")

        # 2. Reset Game
        req_reset = urllib.request.Request(
            f"{server_url}/api/reset", data=json.dumps({}).encode("utf-8"), headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_reset) as response:
            print("Server game reset. New deck is now active!")

    except Exception as e:
        print(f"Note: Could not upload to server (is it running?): {e}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    os.chdir(project_root)  # Ensure we run from root for data/cards.json access
    parse_and_validate_deck("tests/decktest.txt")
