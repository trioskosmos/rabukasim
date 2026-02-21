import json
from collections import OrderedDict


def merge_pseudocode():
    master_path = "audit_master.json"
    manual_path = "data/manual_pseudocode.json"

    with open(master_path, "r", encoding="utf-8") as f:
        master = json.load(f)

    with open(manual_path, "r", encoding="utf-8") as f:
        manual = json.load(f, object_pairs_hook=OrderedDict)

    added_count = 0
    for item in master:
        card_no = item["card_no"]
        if card_no not in manual:
            manual[card_no] = {"pseudocode": item["manual_pseudocode"]}
            added_count += 1

    if added_count > 0:
        # Save back with proper formatting
        with open(manual_path, "w", encoding="utf-8") as f:
            json.dump(manual, f, indent=2, ensure_ascii=False)
        print(f"Successfully added {added_count} missing cards to {manual_path}")
    else:
        print("No missing cards found.")


if __name__ == "__main__":
    merge_pseudocode()
