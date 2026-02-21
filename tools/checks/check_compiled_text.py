import json


def check_compiled_text():
    try:
        with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check first 5 members
        print("--- Checking Members ---")
        count = 0
        for k, v in data.get("member_db", {}).items():
            if v.get("abilities"):
                print(f"ID {k}: {v['abilities'][0].get('raw_text')}")
                count += 1
            if count >= 5:
                break

    except FileNotFoundError:
        print("cards_compiled.json not found.")


if __name__ == "__main__":
    check_compiled_text()
