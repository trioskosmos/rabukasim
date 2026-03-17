import json
import os
import sys

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "engine_rust_src"))

try:
    import engine_rust
except ImportError:
    print("Failed to import engine_rust")
    sys.exit(1)


def run_test():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        json_str = f.read()

    db = engine_rust.PyCardDatabase(json_str)

    # Identify ID for PL!N-bp1-002-P
    # We can check via Python lookup or just guess it logic.
    # Usually:
    #   PL!N-bp1-002-R+ -> Base ID
    #   Variants share Base ID? Or use high bits?
    # Let's inspect the DB members via Python wrapper if possible, or just search the JSON.

    # Parse json to find the ID mapping manually
    data = json.loads(json_str)
    target_card_no = "PL!N-bp1-002-P"
    target_id = -1

    # Helper to parse ID (mimic Rust/Python logic)
    # Rust logic is complex, usually (product << 20) | (card_no)
    # But usually just finding the entry is enough.

    # Let's try to find it in the "members" map of the loaded DB?
    # engine_rust.PyCardDatabase has 'has_member(id)'

    # Parse json to find the ID mapping manually
    data = json.loads(json_str)
    target_card_no = "PL!N-bp1-002-P"
    target_id = -1

    found = False

    # Search member_db
    if "member_db" in data:
        for mid, mdata in data["member_db"].items():
            if mdata.get("card_no") == target_card_no:
                print(f"Found {target_card_no} in member_db ID {mid}")
                target_id = int(mid)
                found = True
                break

    if not found and "live_db" in data:
        for lid, ldata in data["live_db"].items():
            if ldata.get("card_no") == target_card_no:
                print(f"Found {target_card_no} in live_db ID {lid}")
                target_id = int(lid)
                found = True
                break

    if not found:
        print(f"Card {target_card_no} not found in compiled JSON!")
        return

    # Create Game
    gs = engine_rust.PyGameState(db)

    # Setup Hand with the card
    # We need the INTEGER ID.
    # If it's a variant, it might share the ID?
    # In Rust `CardDatabase::from_json`, variants are expanded.
    # If `rare_list` is used, they get independent IDs.

    # Let's iterate ALL members in DB to find it.
    ids = db.get_member_ids()  # We need to expose this or iterate
    # Actually PyCardDatabase has get_member_ids (I added it!)
    ids = db.get_member_ids()

    p_id = 0
    for i in ids:
        # We can't easily get the card_no back from Rust via PyO3 without full bindings
        # But we can try to guess or use the python map
        pass

    # Hack: Just use the base ID for 002.
    # BP01-002?
    # Product 1?
    # Let's just assume we play the base card and see if it works.

    # But wait, user specifically said P version.
    # If P version has a bug, it might be that it wasn't expanded correctly!

    print("Checking if variants are loaded...")
    # We will rely on Python side to confirm ID.

    # ... (Actual simulation later)

    print("Test Setup Complete")


if __name__ == "__main__":
    run_test()
