import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.benchmark_decks import parse_deck


def debug_deck():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_json = json.load(f)

    muse_deck_path = "ai/decks/muse_cup.txt"
    p_deck, p_lives = parse_deck(muse_deck_path, db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {}))

    print(f"Deck Size: {len(p_deck)}")
    print(f"Lives Size: {len(p_lives)}")
    print(f"First 5 Deck: {p_deck[:5]}")
    print(f"First 5 Lives: {p_lives[:5]}")

    # Check if any lives are in range 10000-19999
    live_ids = [lid for lid in p_lives if 10000 <= lid < 20000]
    print(f"Live IDs found in 10000-19999: {len(live_ids)}")

    # Check if any lives are in p_deck
    lives_in_deck = [cid for cid in p_deck if 10000 <= cid < 20000]
    print(f"Live IDs found in p_deck: {len(lives_in_deck)}")


if __name__ == "__main__":
    debug_deck()
