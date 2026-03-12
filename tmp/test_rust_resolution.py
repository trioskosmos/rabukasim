import json
import os
import sys

# Add project root to sys.path
PROJECT_ROOT = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import engine_rust


def normalize_rust_style(code):
    if not code:
        return ""
    return code.replace("＋", "+").replace("－", "-").replace("ー", "-").strip().upper()


def main():
    compiled_path = os.path.join(PROJECT_ROOT, "data", "cards_compiled.json")
    if not os.path.exists(compiled_path):
        print("cards_compiled.json not found")
        return

    with open(compiled_path, "r", encoding="utf-8") as f:
        json_data = f.read()

    db = engine_rust.PyCardDatabase(json_data)

    deck_path = os.path.join(PROJECT_ROOT, "ai", "decks2", "vividworld.txt")
    with open(deck_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    found_members = 0
    found_lives = 0
    missing = []

    total_qty = 0

    # We need to simulate the resolve_deck logic which matches CardDatabase structure
    # But PyCardDatabase might not expose the same iterators easily.
    # Let's check what PyCardDatabase has.
    try:
        print(f"DB Members: {len(db.get_member_ids())}")
        print(f"DB Lives: {len(db.get_live_ids())}")
    except:
        print("Could not get ID lists from db")

    # In Rust utils.rs:
    # db.members.iter().find(|(_, m)| normalize_code(&m.card_no) == norm_code)

    # Let's try to resolve each card from the deck
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if " x " in line:
            code = line.split(" x ")[0].strip()
            qty = int(line.split(" x ")[1].strip())
        else:
            code = line
            qty = 1

        total_qty += qty
        norm_code = normalize_rust_style(code)

        # We can't easily call internal Rust find from here without the same logic
        # But we can check if it exists in the JSON data we loaded
        data = json.loads(json_data)

        found = False
        # Check members
        for mid, mdata in data.get("member_db", {}).items():
            if normalize_rust_style(mdata.get("card_no", "")) == norm_code:
                found_members += qty
                found = True
                break

        if not found:
            for lid, ldata in data.get("live_db", {}).items():
                if normalize_rust_style(ldata.get("card_no", "")) == norm_code:
                    found_lives += qty
                    found = True
                    break

        if not found:
            missing.append(code)

    print(f"Total Quantity in Deck: {total_qty}")
    print(f"Found Members (Qty): {found_members}")
    print(f"Found Lives (Qty): {found_lives}")
    print(f"Total Found (Qty): {found_members + found_lives}")
    print(f"Missing Types: {len(missing)}")
    if missing:
        print(f"Missing: {missing}")


if __name__ == "__main__":
    main()
