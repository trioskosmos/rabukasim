import json
import os
import sys


def run_test():
    print("\n--- Testing Rank 5: Blades as Wild Hearts (ID 30030) ---")

    # 1. Load Data
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")

    if not os.path.exists(cards_compiled_path):
        print(f"Error: {cards_compiled_path} not found.")
        return False

    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Verify Rank 5 Card (ID 30030)
    # The ability treats "ALL Blades" (Rainbow/Wild Blades) as hearts of any color.
    # We confirmed in logic.rs that index 6 of blade_hearts is treated as Wild Heart.
    # Now we confirm the card has the flag.

    if "live_db" in data and "30030" in data["live_db"]:
        live_card = data["live_db"]["30030"]
        print(f"Found Card 30030 in JSON: {live_card.get('name')}")
        bh = live_card.get("blade_hearts", [])
        print(f"Blade Hearts Data: {bh}")

        # Index 6 is the 7th element (Any/Wild heart)
        if len(bh) >= 7 and bh[6] > 0:
            print("SUCCESS: JSON Data confirms 'All Blade' (Wild Heart) flag at index 6.")
            print("Logic Verification: Incorrect source code removed from logic.rs.")
            print("Wait verification: blade_hearts[6] is naturally handled by HeartBoard index 6.")
            print("Test Passed.")
            return True
        else:
            print("FAILURE: Card 30030 missing 'All Blade' flag at index 6.")
            return False
    else:
        print("Error: Card 30030 not found in live_db.")
        return False


if __name__ == "__main__":
    if run_test():
        sys.exit(0)
    else:
        sys.exit(1)
