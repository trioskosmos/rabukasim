import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game.data_loader import CardDataLoader


def debug_loading():
    loader = CardDataLoader("engine/data/cards.json")
    members, lives, energy = loader.load()

    ids = ["PL!S-pr-001-PR", "PL!S-pr-002-PR", "PL!S-pr-003-PR", "PL!S-pr-004-PR"]

    print(f"Loaded {len(members)} members, {len(lives)} lives, {len(energy)} energy.")

    found_count = 0
    for cid, m in members.items():
        if m.card_no in ids:
            print(f"Found {m.card_no} in members with ID {cid}")
            found_count += 1

    print(f"Found {found_count}/{len(ids)} target cards.")


if __name__ == "__main__":
    debug_loading()
