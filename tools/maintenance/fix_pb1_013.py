import json
import os

TARGET_NO = "PL!S-pb1-013-N"
DATA_FILE = "data/cards_compiled.json"


def patch_card():
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    member_db = data.get("member_db", {})
    target_id = None
    target_card = None

    for cid, card in member_db.items():
        if card.get("card_no") == TARGET_NO:
            target_id = cid
            target_card = card
            break

    if not target_card:
        print(f"Card {TARGET_NO} not found.")
        return

    print(f"Found {TARGET_NO} (ID: {target_id})")

    # Patch Effects
    abilities = target_card.get("abilities", [])
    if not abilities:
        print("No abilities found.")
        return

    # Assuming Ability 0 is the OnPlay one
    ability = abilities[0]
    effects = ability.get("effects", [])

    # Effect 0: LOOK_DECK
    # Change params["from"] to "deck" (was "discard")
    if len(effects) > 0 and effects[0].get("effect_type") == 4:
        print("Patching Effect 0 (LOOK_DECK)...")
        if "params" not in effects[0]:
            effects[0]["params"] = {}
        effects[0]["params"]["from"] = "deck"
        # Also ensure value is 4 (it was 4)

    # Effect 1: LOOK_AND_CHOOSE
    # Change "filter": "live" to "req_heart:3:2" (Purple=3, Min=2)
    # This uses the new engine capability we added.
    if len(effects) > 1 and effects[1].get("effect_type") == 27:
        print("Patching Effect 1 (LOOK_AND_CHOOSE)...")
        params = effects[1].get("params", {})
        if "filter" in params:
            print(f"Replacing filter '{params['filter']}' with 'req_heart:3:2'")
            params["filter"] = "req_heart:3:2"
        else:
            print("Adding filter 'req_heart:3:2'")
            params["filter"] = "req_heart:3:2"

        # Update params
        effects[1]["params"] = params

    # Save back
    # We need to write the WHOLE db back.
    # Be careful with encoding.
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=None)  # Compact save to keep size down? Or indent=2?
            # Original file was likely compact or 2.
            # cards_compiled.json is usually compact-ish. Inspect detail showed indent=2.
            # Let's use indent=2 to be safe/readable, or None if it's huge.
            # It's 2MB. Indent=2 makes it larger but safer for diffs.
            # Let's use separators=(',', ':') for compact.
    except Exception as e:
        print(f"Error saving: {e}")
        return

    print("Successfully patched cards_compiled.json")


if __name__ == "__main__":
    patch_card()
