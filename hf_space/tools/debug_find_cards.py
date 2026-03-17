import json
import os


def find_cards():
    path = "data/cards_compiled.json"
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    member_db = data.get("member_db", {})

    # Check 4596
    c4596 = member_db.get("4596", {})
    print(f"Card 4596: {c4596.get('name')} (ID: 4596)")
    for i, ab in enumerate(c4596.get("abilities", [])):
        print(f"  Ab {i}: Trigger {ab.get('trigger')} - {ab.get('pseudocode', '')}")

    on_play = []
    activated = []

    for cid, card in member_db.items():
        abs = card.get("abilities", [])
        if any(ab.get("trigger") == 1 for ab in abs):
            on_play.append((cid, card.get("name")))
        if any(ab.get("trigger") == 7 for ab in abs):
            activated.append((cid, card.get("name")))

    print("\nOnPlay Cards (first 10):")
    for cid, name in on_play[:10]:
        print(f"  {cid}: {name}")

    print("\nActivated Cards (first 10):")
    for cid, name in activated[:10]:
        print(f"  {cid}: {name}")


if __name__ == "__main__":
    find_cards()
