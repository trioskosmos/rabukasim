import json
import os


def main():
    compiled_path = "data/cards_compiled.json"
    deck_path = "ai/decks/muse_cup.txt"

    if not os.path.exists(compiled_path):
        print(f"Error: {compiled_path} not found")
        return

    with open(compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    member_map = {v["card_no"]: int(k) for k, v in data["member_db"].items()}
    live_map = {v["card_no"]: int(k) for k, v in data["live_db"].items()}

    members = []
    lives = []

    if not os.path.exists(deck_path):
        print(f"Error: {deck_path} not found")
        return

    with open(deck_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or " x " not in line:
                continue
            card_no, count_str = line.split(" x ")
            count = int(count_str)

            if card_no in member_map:
                members.extend([member_map[card_no]] * count)
            elif card_no in live_map:
                lives.extend([live_map[card_no]] * count)
            else:
                print(f"Warning: Card {card_no} not found in DB")

    print("--- PARSED DECK ---")
    print(f"Members ({len(members)}): {members}")
    print(f"Lives ({len(lives)}): {lives}")


if __name__ == "__main__":
    main()
