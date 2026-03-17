import json


def analyze_counts():
    try:
        compiled_path = "engine/data/cards_compiled.json"
        raw_path = "data/cards.json"

        with open(compiled_path, "r", encoding="utf-8") as f:
            compiled_data = json.load(f)

        with open(raw_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        members = compiled_data.get("member_db", {})
        lives = compiled_data.get("live_db", {})
        compiled_total = len(members) + len(lives)
        raw_total = len(raw_data)

        print(f"Raw Cards: {raw_total}")
        print(f"Compiled Total: {compiled_total} (Members: {len(members)}, Lives: {len(lives)})")

        # Check intersection
        compiled_ids = set(members.keys()) | set(lives.keys())
        raw_ids = set(raw_data.keys())

        only_in_compiled = compiled_ids - raw_ids
        only_in_raw = raw_ids - compiled_ids

        print(f"IDs in Compiled but not Raw: {len(only_in_compiled)}")
        if len(only_in_compiled) > 0:
            print(f"Examples: {list(only_in_compiled)[:5]}")

        print(f"IDs in Raw but not Compiled: {len(only_in_raw)}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    analyze_counts()
