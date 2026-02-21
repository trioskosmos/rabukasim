import json
import os


def list_names():
    file_path = "data/cards_compiled.json"
    if not os.path.exists(file_path):
        print("Error: data/cards_compiled.json not found")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    names = set()
    for m in data.get("member_db", {}).values():
        if "name" in m:
            names.add(m["name"])

    for n in sorted(list(names)):
        print(n)


if __name__ == "__main__":
    list_names()
