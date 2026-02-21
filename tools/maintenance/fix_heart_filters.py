import json

DATA_FILE = "data/cards_compiled.json"


def fix_heart_filters():
    print(f"Loading {DATA_FILE}...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Patch targets:
    # 013 (Heart04>=2) -> req_heart:3:2
    # 014 (Heart02>=2) -> req_heart:1:2
    # 015 (Heart05>=2) -> req_heart:4:2

    targets = {"PL!S-pb1-013-N": "req_heart:3:2", "PL!S-pb1-014-N": "req_heart:1:2", "PL!S-pb1-015-N": "req_heart:4:2"}

    modified = False

    for cid, card in data.get("member_db", {}).items():
        cno = card.get("card_no")
        if cno in targets:
            print(f"Found {cno} (ID: {cid})")
            abilities = card.get("abilities", [])

            # Assuming Effect 0 is LOOK_DECK (4) and Effect 1 is LOOK_AND_CHOOSE (27)
            # based on my previous analysis of 013.
            # Need to be careful slightly, but they are likely identical structure.

            for ab in abilities:
                effects = ab.get("effects", [])

                # Patch LOOK_DECK (Effect Type 4)
                # Ensure checking from DECK
                for eff in effects:
                    if eff.get("effect_type") == 4:
                        if eff.get("params", {}).get("from") != "deck":
                            print("  - Fixing LOOK_DECK 'from' parameter to 'deck'")
                            if "params" not in eff:
                                eff["params"] = {}
                            eff["params"]["from"] = "deck"
                            modified = True

                    # Patch LOOK_AND_CHOOSE (Effect Type 27)
                    if eff.get("effect_type") == 27:
                        target_filter = targets[cno]
                        current_filter = eff.get("params", {}).get("filter")

                        if current_filter != target_filter:
                            print(f"  - Updating filter: '{current_filter}' -> '{target_filter}'")
                            if "params" not in eff:
                                eff["params"] = {}
                            eff["params"]["filter"] = target_filter
                            modified = True

    if modified:
        print("Saving changes to cards_compiled.json...")
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Successfully patched cards.")
    else:
        print("No changes needed.")


if __name__ == "__main__":
    fix_heart_filters()
