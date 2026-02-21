import os
import re
import sys

# Add project root to path
sys.path.insert(0, os.getcwd())

from engine.game.card_loader import CardDataLoader


def extract_deck():
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

    # Regex to find title='ID : Name' ... <span class='num'>COUNT</span>
    # We look for the pattern: title="PL!..." ... class="num">N</span>

    # Let's use a simpler approach: multiple regexes
    # 1. Find all card-view divs

    deck_list = []
    print("Found cards:")

    # Find all occurrences of potential card entries
    # Pattern: title="(PL![^ ]+)" ... class="num">(\d+)

    # Note: re.DOTALL is important if newlines exist
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
            # Ignore count 12 if it's the energy deck (usually 12 cards)
            # Actually, decktest.txt separates them.
            # The HTML shows "エネルギーデッキ" then PL!SP-bp1-030-SECE x12
            # We want main deck only? The Main Deck has 60 cards usually.
            # Wait, the deck list in HTML has Main Deck and Energy Deck.
            # card ID 200 is standard energy.

            # Let's filter: if it's the 12-card energy member, skip/handle separately?
            # Standard game logic sets energy deck to ID 200.
            # If this is a member card being used as energy, we might need to handle it.
            # But usually benchmark uses 200.

            # Let's perform a check for main deck size vs energy deck

            # For now, just print what we found
            print(f"{no}: {cid} x{count}")
            deck_list.extend([cid] * count)
        else:
            print(f"WARNING: Could not find card {no}")

    print(f"\nTotal Cards: {len(deck_list)}")
    print(f"Deck List: {deck_list}")


if __name__ == "__main__":
    extract_deck()
