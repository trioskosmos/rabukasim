import json
import os


def find_card():
    path = "data/cards_compiled.json"
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cards = []
    if "member_db" in data:
        members = data["member_db"]
        if isinstance(members, dict):
            cards.extend(members.values())
        elif isinstance(members, list):
            cards.extend(members)

    # Use "live_db" instead of "live_cards"
    if "live_db" in data:
        lives = data["live_db"]
        if isinstance(lives, dict):
            cards.extend(lives.values())
        elif isinstance(lives, list):
            cards.extend(lives)

    target_prefix = "PL!HS-bp1-003"

    output = []
    found = False
    for card in cards:
        cno = card.get("no") or card.get("card_no")
        # Try both 'id' and 'card_id'
        cid = card.get("id") or card.get("card_id")

        if cno and target_prefix in cno:
            output.append(f"Found Match: No='{cno}' ID={cid}")
            found = True

    with open("card_info_utf8.txt", "w", encoding="utf-8") as f:
        for line in output:
            f.write(line + "\n")
            print(line)


if __name__ == "__main__":
    find_card()
