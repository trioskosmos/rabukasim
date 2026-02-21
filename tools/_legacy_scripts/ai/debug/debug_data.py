import json


def main():
    print("Loading DB...")
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db = json.load(f)

    target_no = "PL!-sd1-014-SD"
    target_id = "0"

    print(f"Scanning member_db for CardNo '{target_no}' or ID '{target_id}'...")

    found_id = False
    found_no = False

    if target_id in db.get("member_db", {}):
        print(f"!!! FOUND ID {target_id} in member_db object keys!")
        found_id = True

    for cid, data in db.get("member_db", {}).items():
        if str(cid) == target_id:
            print(f"!!! FOUND ID {target_id} in member_db iteration!")

        if data.get("card_no") == target_no:
            print(f"!!! FOUND CardNo {target_no} in member_db value! ID: {cid}")
            found_no = True

    if not found_id and not found_no:
        print("Scanned entire member_db. Neither ID nor CardNo found.")

    print("\nChecking live_db for sanity...")
    if target_id in db.get("live_db", {}):
        print(f"Confirmed ID {target_id} is in live_db.")


if __name__ == "__main__":
    main()
