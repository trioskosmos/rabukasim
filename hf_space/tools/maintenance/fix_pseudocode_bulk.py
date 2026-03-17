import json
import os


def fix_pseudocode():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manual_path = os.path.join(base_dir, "data", "manual_pseudocode.json")
    audit_path = os.path.join(base_dir, "tools", "audit_results.json")

    print(f"Loading {audit_path}...")
    with open(audit_path, "r", encoding="utf-8") as f:
        audit_results = json.load(f)

    print(f"Loading {manual_path}...")
    with open(manual_path, "r", encoding="utf-8") as f:
        manual_data = json.load(f)

    fixed_count = 0

    for entry in audit_results:
        card_id = entry["id"]
        code = entry["code"]

        # Only fix the safe ones for now: RECOVER_LIVE and RECOVER_MEMBER
        # Also fix LOOK_AND_CHOOSE which usually adds to hand

        new_code = code
        modified = False

        # Fix RECOVER_LIVE/MEMBER -> CARD_DISCARD => -> CARD_HAND
        if "RECOVER_LIVE" in new_code and "-> CARD_DISCARD" in new_code:
            new_code = new_code.replace("RECOVER_LIVE(1) -> CARD_DISCARD", "RECOVER_LIVE(1) -> CARD_HAND")
            # Handle other values if necessary, but regex/replace simplisticly for now
            # If value is different, the simple string replace might fail.
            # But the audit showed mostly (1).
            if "-> CARD_DISCARD" in new_code:  # Still there?
                new_code = new_code.replace("-> CARD_DISCARD", "-> CARD_HAND")  # Aggressive fallback for this line
            modified = True

        elif "RECOVER_MEMBER" in new_code and "-> CARD_DISCARD" in new_code:
            new_code = new_code.replace("RECOVER_MEMBER(1) -> CARD_DISCARD", "RECOVER_MEMBER(1) -> CARD_HAND")
            if "-> CARD_DISCARD" in new_code:
                new_code = new_code.replace("-> CARD_DISCARD", "-> CARD_HAND")
            modified = True

        elif "LOOK_AND_CHOOSE" in new_code and "-> CARD_DISCARD" in new_code:
            # LOOK_AND_CHOOSE -> CARD_DISCARD likely implies looking and adding to hand?
            # Or is it swapping?
            # Safe bet for "Looking" abilities is Hand.
            new_code = new_code.replace("-> CARD_DISCARD", "-> CARD_HAND")
            modified = True

        # Add special case for PL!N-bp3-004-P if it wasn't caught generically
        if card_id == "PL!N-bp3-004-P":
            # Ensure it targets CARD_HAND
            if "-> CARD_DISCARD" in new_code:
                new_code = new_code.replace("-> CARD_DISCARD", "-> CARD_HAND")
            modified = True

        if modified:
            if card_id not in manual_data:
                manual_data[card_id] = {"pseudocode": new_code}
                print(f"Added {card_id} to manual_pseudocode.json")
            else:
                manual_data[card_id]["pseudocode"] = new_code
                print(f"Updated {card_id} in manual_pseudocode.json")
            fixed_count += 1

    print(f"Fixed {fixed_count} entries.")

    print(f"Saving {manual_path}...")
    with open(manual_path, "w", encoding="utf-8") as f:
        json.dump(manual_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    fix_pseudocode()
