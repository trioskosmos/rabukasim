import json
import re
import shutil


def standardize():
    file_path = "data/manual_pseudocode.json"
    backup_path = "data/manual_pseudocode.backup.json"

    shutil.copy(file_path, backup_path)
    print(f"Backed up to {backup_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    REPLACEMENTS = {
        "ADD_HAND(": "ADD_TO_HAND(",
        "MOVE_HAND(": "ADD_TO_HAND(",
        "MOVE_TO_HAND(": "ADD_TO_HAND(",
        "TAP_PLAYER(": "TAP_MEMBER(",
        "TAP_SELF": "TAP_MEMBER",  # Often appears without parens in COST
        "CHARGE_SELF": "ENERGY_CHARGE",
        "CHARGE_ENERGY": "ENERGY_CHARGE",
        "MOVE_DISCARD(": "MOVE_TO_DISCARD(",
        "REMOVE_SELF": "MOVE_TO_DISCARD",
        "SWAP_SELF": "SWAP_ZONE",
        # 'DISCARD_HAND': 'LOOK_AND_CHOOSE', # Too risky to replace globally as it might be COST
        "SELECT_LIMIT(": "REDUCE_LIVE_SET_LIMIT(",
        "POWER_UP(": "BUFF_POWER(",
        "REDUCE_SET_LIMIT(": "REDUCE_LIVE_SET_LIMIT(",
        "REDUCE_LIMIT(": "REDUCE_LIVE_SET_LIMIT(",
        "REDUCE_HEART(": "REDUCE_HEART_REQ(",
        "PREVENT_LIVE(": "RESTRICTION(",
        "MOVE_DECK(": "MOVE_TO_DECK(",
        "OPPONENT_CHOICE(": "OPPONENT_CHOOSE(",
        "SET_BASE_BLADES(": "SET_BLADES(",
        "GRANT_HEARTS(": "ADD_HEARTS(",
        "GRANT_HEART(": "ADD_HEARTS(",
        "SELECT_REVEALED(": "LOOK_AND_CHOOSE(",
        "LOOK_AND_CHOOSE_REVEALED(": "LOOK_AND_CHOOSE(",
        "CHANGE_BASE_HEART(": "TRANSFORM_HEART(",
        "SELECT_LIVE_CARD(": "SELECT_LIVE(",
        "POSITION_CHANGE(": "MOVE_MEMBER(",
        "INCREASE_HEART(": "INCREASE_HEART_COST(",
        "CHANGE_YELL_BLADE_COLOR(": "TRANSFORM_COLOR(",
    }

    modified_count = 0
    for card_id, entry in data.items():
        if "pseudocode" not in entry:
            continue

        original = entry["pseudocode"]
        text = original

        # 1. Apply canonical replacements
        # We start with specific function calls to avoid accidental substring matches
        for old, new in REPLACEMENTS.items():
            if old in text:
                text = text.replace(old, new)

        # 2. Fix spacing (Keyword:Value) -> (Keyword: Value)
        # We carefully look for KEYWORD: immediately followed by non-space
        for kw in ["TRIGGER", "COST", "CONDITION", "EFFECT"]:
            text = re.sub(f"{kw}:(?=[^\\s])", f"{kw}: ", text)

        # 3. Standardize OPTION format if needed (not converting to multiline yet as agreed)

        if text != original:
            entry["pseudocode"] = text
            modified_count += 1

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Standardized {modified_count} cards.")


if __name__ == "__main__":
    standardize()
