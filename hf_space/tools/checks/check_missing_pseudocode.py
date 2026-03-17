import json


def check_missing():
    with open("audit_master.json", "r", encoding="utf-8") as f:
        master = json.load(f)

    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        manual = json.load(f)

    master_nos = set(item["card_no"] for item in master)
    manual_nos = set(manual.keys())

    missing = master_nos - manual_nos
    # Filter out LL- cards if they are not meant to be in manual_pseudocode
    # (Checking the file, LL- cards are there, so keep them)

    print(f"Master unique cards: {len(master_nos)}")
    print(f"Manual unique cards: {len(manual_nos)}")
    print(f"Missing from Manual: {len(missing)}")

    if missing:
        print("\nMissing Cards (first 20):")
        for m in sorted(list(missing))[:20]:
            print(m)


if __name__ == "__main__":
    check_missing()
