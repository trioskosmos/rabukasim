import json


def verify():
    print("Loading compiled data...")
    with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    print("Data loaded.")

    # Check PL!SP-bp4-025-L (Live Card)
    print("\n--- Verifying PL!SP-bp4-025-L ---")
    found_live = False
    for k, v in data["live_db"].items():
        if v["card_no"] == "PL!SP-bp4-025-L":
            print(f"Found in live_db[{k}]")
            found_live = True
            found_moved = False
            found_set_blades = False
            for ab in v["abilities"]:
                for cond in ab["conditions"]:
                    if cond["type"] == 29:  # HAS_MOVED
                        found_moved = True
                        print("  [OK] Found HAS_MOVED condition")
                for eff in ab["effects"]:
                    if eff["effect_type"] == 31:  # SET_BLADES
                        found_set_blades = True
                        print(f"  [OK] Found SET_BLADES effect (val={eff.get('value')})")

            if not found_moved:
                print("  [FAIL] Missing HAS_MOVED")
            if not found_set_blades:
                print("  [FAIL] Missing SET_BLADES")
            break

    if not found_live:
        print("PL!SP-bp4-025-L NOT FOUND in live_db")

    # Check LL-PR-004-PR (Member Card)
    print("\n--- Verifying LL-PR-004-PR ---")
    found_member = False
    for k, v in data["member_db"].items():
        if v["card_no"] == "LL-PR-004-PR":
            print(f"Found in member_db[{k}]")
            found_member = True
            found_flavor = False
            for ab in v["abilities"]:
                for eff in ab["effects"]:
                    if eff["effect_type"] == 99:  # FLAVOR_ACTION
                        found_flavor = True
                        print(f"  [OK] Found FLAVOR_ACTION effect (params={eff.get('params')})")

            if not found_flavor:
                print("  [FAIL] Missing FLAVOR_ACTION")
            # Dump abilities for debugging if fail
            if not found_flavor:
                print(f"  Abilities: {v['abilities']}")
            break

    if not found_member:
        print("LL-PR-004-PR NOT FOUND in member_db")
        # Optimization: Search similar IDs
        print("Searching for similar IDs...")
        for k, v in list(data["member_db"].items())[:500]:  # Check first 500
            if "LL-" in v["card_no"]:
                print(f"  Found LL- card: {v['card_no']}")


if __name__ == "__main__":
    verify()
