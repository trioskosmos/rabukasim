import json
import re


def find_examples():
    try:
        with open("data/cards.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        examples = []

        # We want varied groups
        groups_found = set()

        for cid, card in data.items():
            ability = card.get("ability", "")
            if not ability:
                continue

            # Look for "『Group』... 場合" pattern roughly
            # or just ability containing both '『' and '場合'
            if "『" in ability and "場合" in ability:
                # Extract group
                match = re.search(r"『(.*?)』", ability)
                if match:
                    group = match.group(1)
                    if group not in groups_found or len(examples) < 5:
                        examples.append({"id": cid, "name": card.get("name"), "group": group, "text": ability})
                        groups_found.add(group)

            if len(examples) >= 5 and len(groups_found) >= 3:
                break

        for i, ex in enumerate(examples):
            print(f"--- Example {i + 1} ---")
            print(f"ID: {ex['id']}")
            print(f"Name: {ex['name']}")
            print(f"Group: {ex['group']}")
            print(f"Text: {ex['text']}")
            print("")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    find_examples()
