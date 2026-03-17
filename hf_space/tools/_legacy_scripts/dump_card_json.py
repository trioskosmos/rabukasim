import json
import os


def dump_card():
    path = "engine/tests/data/cards_compiled.json"
    # Try finding it in data/ if not in engine/tests/data
    if not os.path.exists(path):
        path = "data/cards_compiled.json"

    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Member DB is typically key "members" or just a dict?
    # Based on GameState, it loads "members" key if it exists, or assumes root is dict check.
    # Actually GameState loads: `data = json.load(...)` then `self.member_db = ...`
    # Let's inspect the structure of loaded data.

    print(f"Root keys: {data.keys()}")
    members = data.get("members", {})
    if not members:
        # Maybe it's a list or root dict?
        # Assuming typical structure.
        pass

    print(f"Members type: {type(members)}")
    if isinstance(members, dict):
        print(f"first key: {list(members.keys())[0]}")
        first_val = members[list(members.keys())[0]]
        print(f"first val keys: {first_val.keys()}")
    elif isinstance(members, list):
        print(f"list len: {len(members)}")
        print(f"first item: {members[0] if members else 'empty'}")

    target_id = "561"
    # Convert to int if keys are ints (in dict logic? no json keys are always strings)
    # But if it's a list, we iterate?

    if isinstance(members, dict):
        if target_id in members:
            print(json.dumps(members[target_id], indent=2, ensure_ascii=False))
        else:
            print(f"ID {target_id} not in members keys")

        found = False
        for cid, card in members.items():
            if card.get("card_no") == "PL!S-pb1-013-N":
                print(json.dumps(card, indent=2, ensure_ascii=False))
                found = True
                break
        if not found:
            print("Card PL!S-pb1-013-N not found in JSON")


if __name__ == "__main__":
    dump_card()
