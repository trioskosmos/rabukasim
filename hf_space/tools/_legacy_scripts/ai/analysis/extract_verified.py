import json
import os

REPORT_PATH = "docs/MASTER_REPORT.md"
OUTPUT_PATH = "data/verified_card_pool.json"


def extract_verified():
    if not os.path.exists(REPORT_PATH):
        print(f"Report not found at {REPORT_PATH}")
        return

    verified_ids = []

    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            # Table row format: | Card No | ... | Status | ...
            if "|" not in line:
                continue

            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 5:
                continue

            card_id = parts[1]
            status = parts[4]  # Index 4 based on splitting: empty, id, name, complexity, status, ...

            # Check for "Verified" keyword in status (bold or plain)
            # Also include "Passed" and "Fixed" as valid statuses
            if any(k in status for k in ["Verified", "Passed", "Fixed"]):
                verified_ids.append(card_id)

    # Remove duplicates and sort
    verified_ids = sorted(list(set(verified_ids)))

    print(f"Found {len(verified_ids)} verified cards total.")

    # Load DB to distinguish Members/Lives
    try:
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            db_data = json.load(f)
        member_nos = set(c["card_no"] for c in db_data.get("member_db", {}).values())
        live_nos = set(c["card_no"] for c in db_data.get("live_db", {}).values())
    except Exception as e:
        print(f"Warning: Could not load cards_compiled.json for categorization: {e}")
        member_nos = set()
        live_nos = set()

    verified_members = []
    verified_lives = []

    # 1. From Report
    for vid in verified_ids:
        # Prioritize ID pattern check as it is definitive in this schema
        is_live_id = "-L" in vid or vid.startswith("L-")

        if is_live_id:
            verified_lives.append(vid)
        elif vid in live_nos:
            verified_lives.append(vid)
        elif vid in member_nos:
            verified_members.append(vid)
        else:
            # Default fallback
            verified_members.append(vid)

    # 2. Auto-include Vanilla Lives from DB
    vanilla_count = 0
    if "live_db" in db_data:
        for card_key, card_def in db_data["live_db"].items():
            # Check for empty abilities list
            if len(card_def.get("abilities", [])) == 0:
                c_no = card_def.get("card_no")
                if c_no and c_no not in verified_lives:
                    verified_lives.append(c_no)
                    vanilla_count += 1

    print(f"  - Auto-included Vanilla Lives: {vanilla_count}")

    print(f"  - Members: {len(verified_members)}")
    print(f"  - Lives:   {len(verified_lives)}")

    output_data = {
        "verified_abilities": verified_members,
        "verified_lives": verified_lives,
        "vanilla_lives": ["L-001"],  # Keep as fallback
    }

    # Save to data/ for record
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    print(f"Saved to {OUTPUT_PATH}")

    # Save to root for VectorEnv/Numba engine
    root_pool_path = "verified_card_pool.json"
    with open(root_pool_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    print(f"Saved to {root_pool_path}")


if __name__ == "__main__":
    extract_verified()
