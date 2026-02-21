import os
import re
import sys

# Add project root to path (redundant if running from root, but safe)
sys.path.insert(0, os.getcwd())

from engine.game.card_loader import CardDataLoader


def extract_deck():
    print(f"CWD: {os.getcwd()}")
    print(f"Path: {sys.path[:3]}")

    # Load IDs
    try:
        loader = CardDataLoader("engine/data/cards.json")
        m_db, l_db, e_db = loader.load()
    except Exception as e:
        print(f"Failed to load cards: {e}")
        return

    card_map = {}
    for c in m_db.values():
        card_map[c.card_no] = c.card_id
    for c in l_db.values():
        card_map[c.card_no] = c.card_id

    # Also add map for "+" vs "＋"
    keys = list(card_map.keys())
    for k in keys:
        if "+" in k:
            card_map[k.replace("+", "＋")] = card_map[k]

    # Parse decktest.txt
    try:
        with open("tests/decktest.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Failed to read decktest.txt: {e}")
        return

    deck_list = []
    print("Found cards:")

    matches = re.findall(r'title="(PL![^\s"]+)\s*:.*?.class="num">(\d+)</span>', content, re.DOTALL)

    for no, count in matches:
        no = no.strip()
        cid = card_map.get(no)
        if not cid:
            # Try replacing fullwidth plus
            if "＋" in no:
                cid = card_map.get(no.replace("＋", "+"))

        if cid:
            count = int(count)
            print(f"{no}: {cid} x{count}")
            deck_list.extend([cid] * count)
        else:
            print(f"WARNING: Could not find card {no}")

    print(f"\nTotal Cards: {len(deck_list)}")
    print(f"Deck List: {deck_list}")


if __name__ == "__main__":
    extract_deck()
