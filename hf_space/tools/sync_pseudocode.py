import json
import os
import sys

# Ensure we can import from local modules
sys.path.append(os.getcwd())

from tools.decompile_bytecode import decompile


def main():
    compiled_path = "data/cards_compiled.json"
    raw_path = "engine/data/cards.json"

    if not os.path.exists(compiled_path) or not os.path.exists(raw_path):
        print("Missing data files.")
        return

    with open(compiled_path, "r", encoding="utf-8") as f:
        compiled_data = json.load(f)
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_cards = json.load(f)

    # Map to store combined pseudocode
    card_to_pcode = {}

    def process_db(db):
        for card_id, card_data in db.items():
            card_no = card_data.get("card_no")
            if not card_no:
                continue

            abilities = card_data.get("abilities", [])
            pcodes = []
            for ab in abilities:
                p = decompile(ab.get("bytecode", []))
                if p:
                    pcodes.append(p)

            card_to_pcode[card_no] = "\n\n".join(pcodes)

    process_db(compiled_data.get("member_db", {}))
    process_db(compiled_data.get("live_db", {}))

    # Update raw cards
    count = 0
    for card_no, pcode in card_to_pcode.items():
        if card_no in raw_cards:
            raw_cards[card_no]["pseudocode"] = pcode
            count += 1

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_cards, f, ensure_ascii=False, indent=4)

    print(f"Successfully synced {count} cards in {raw_path}")


if __name__ == "__main__":
    main()
