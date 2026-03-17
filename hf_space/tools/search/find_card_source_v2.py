import json


def find_source_v2():
    path = "data/cards.json"
    target = "PL!N-bp1-002-P"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check top level
    if target in data:
        print(f"Found at Top Level: {target}")
        print(json.dumps(data[target], indent=2, ensure_ascii=False))
        return

    # Check rare_lists
    for key, val in data.items():
        if "rare_list" in val:
            for rare_item in val["rare_list"]:
                if rare_item.get("card_no") == target:
                    print(f"Found in rare_list of {key}")
                    print(json.dumps(rare_item, indent=2, ensure_ascii=False))
                    print("--- Parent Data ---")
                    # print(json.dumps(val, indent=2, ensure_ascii=False))
                    return

    print("Card not found in raw source.")


if __name__ == "__main__":
    find_source_v2()
