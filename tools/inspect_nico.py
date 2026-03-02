import json


def run():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    mdb = data["member_db"]
    nico_keys = ["103", "4199", "247"]

    for k in nico_keys:
        if k in mdb:
            c = mdb[k]
            print(f"Key: {k}")
            print(f"  Name: {c.get('name')}")
            print(f"  Card No: {c.get('card_no')}")
            abs = c.get("abilities", [])
            print(f"  Abilities count: {len(abs)}")
            for i, ab in enumerate(abs):
                bc = ab.get("bytecode", [])
                print(f"    Ability {i}:")
                print(f"      Trigger: {ab.get('trigger')}")
                print(f"      Bytecode: {bc}")
                if bc and bc[0] == 10:
                    print("      WARNING: Bytecode starts with 10 (DRAW)!")
            print("-" * 20)
        else:
            print(f"Key {k} not found in member_db")


run()
