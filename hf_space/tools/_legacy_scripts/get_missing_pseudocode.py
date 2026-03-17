import json


def get_missing_entries():
    with open("audit_master.json", "r", encoding="utf-8") as f:
        master = json.load(f)

    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        manual = json.load(f)

    master_dict = {item["card_no"]: item["manual_pseudocode"] for item in master}
    missing_keys = set(master_dict.keys()) - set(manual.keys())

    missing_entries = {k: {"pseudocode": master_dict[k]} for k in sorted(list(missing_keys))}
    print(json.dumps(missing_entries, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    get_missing_entries()
