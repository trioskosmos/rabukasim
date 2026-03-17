import json
import os
import sys
from collections import Counter

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.game.deck_utils import UnifiedDeckParser


def extract_deck_data(content, card_db):
    """
    Parses HTML content to extract card IDs and quantities using UnifiedDeckParser.
    Returns (main_deck, energy_deck, type_counts, errors)
    """
    parser = UnifiedDeckParser(card_db)
    results = parser.extract_from_content(content)
    if not results:
        return [], [], {"Member": 0, "Live": 0, "Energy": 0, "Unknown": 0}, ["No deck found"]

    d = results[0]
    return d["main"], d["energy"], d["type_counts"], d["errors"]


def parse_and_validate_deck(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Load card DB
    card_db = {}
    db_path = "data/cards.json"
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            card_db = json.load(f)

    main_deck, energy_deck, type_counts, errors = extract_deck_data(content, card_db)

    # Output Report
    report_path = "deck_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"=== Deck Verification Report for {os.path.basename(file_path)} ===\n")
        f.write(f"Total Cards: {len(main_deck) + len(energy_deck)}\n")
        f.write(
            f"Breakdown: Member: {type_counts.get('Member', 0)} | Live: {type_counts.get('Live', 0)} | Energy: {type_counts.get('Energy', 0)}\n"
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
            f.write("VALID DECK\n")
        else:
            f.write("DECK HAS ISSUES:\n")
            for e in errors:
                f.write(f"- {e}\n")

    print(f"Report written to {report_path}")
    print(f"Total: {len(main_deck)} Main + {len(energy_deck)} Energy")

    # Auto-upload to server if running
    try:
        import urllib.request

        server_url = "http://localhost:8000"
        payload = {"player": 0, "deck": main_deck, "energy_deck": energy_deck}
        req = urllib.request.Request(
            f"{server_url}/api/set_deck",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            print("Successfully sent deck to server.")
    except Exception:
        pass


if __name__ == "__main__":
    # Ensure we are in project root for card_db access
    if os.path.exists("data/cards.json"):
        parse_and_validate_deck("tests/decktest.txt")
    else:
        print("Run from project root.")
