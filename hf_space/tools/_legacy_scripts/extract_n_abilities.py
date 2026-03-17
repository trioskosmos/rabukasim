import json


def extract_abilities():
    with open("engine/data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    target_ids = []
    # Generate IDs for N-sd1-001 to 028
    for i in range(1, 29):
        num = f"{i:03d}"
        # Try both -SD and -P or whatever exists
        # Actually keys in json are exact.
        # list_sd1.py showed PL!N-sd1-001-SD etc.
        target_ids.append(f"PL!N-sd1-{num}-SD")
        # Also parallel?
        # target_ids.append(f"PL!N-sd1-{num}-P")

    for cid in target_ids:
        if cid in data:
            card = data[cid]
            name = card.get("name", "Unknown")
            ability = card.get("ability", "None")
            print(f"ID: {cid} | Name: {name}")
            print(f"Ability: {ability}")
            print("-" * 20)


if __name__ == "__main__":
    extract_abilities()
