import json


def run():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)
    print("Found in cards.json:", "726" in cards)

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        compiled = json.load(f)

    found = False
    for k, v in compiled.items():
        if v.get("card_no") == "PL!HS-sd1-013-SD":
            print("Found in compiled! Key:", k, "Name:", v.get("name"))
            print("Cost:", v.get("cost"), "Type:", v.get("type"))
            print("Abilities:", len(v.get("abilities", [])))
            for ab in v.get("abilities", []):
                print("  Trigger:", ab.get("trigger"))
            found = True
            break

    if not found:
        print("Not found by card_no in compiled.")


run()
