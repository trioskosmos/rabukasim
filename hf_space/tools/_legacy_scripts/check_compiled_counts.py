import json


def check():
    path = "engine/data/cards_compiled.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    targets = ["PL!S-bp2-001-R", "PL!S-pb1-009-R"]
    for t in targets:
        found = False
        for c in data["member_db"].values():
            if c["card_no"] == t:
                print(f"{t}: {len(c['abilities'])} abilities")
                found = True
                print(json.dumps(c["abilities"], indent=2, ensure_ascii=False))
                break
        if not found:
            print(f"{t}: NOT FOUND")


if __name__ == "__main__":
    check()
