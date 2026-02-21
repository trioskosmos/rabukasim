import json
import os
import sys

sys.stdout.reconfigure(line_buffering=True)


def find_cards():
    print("Loading cards_compiled.json...", flush=True)
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    member_db = data.get("member_db", {})
    print(f"Member DB Size: {len(member_db)}")

    # Rank 9: Draw 2, Discard 2
    # Opcode likely: O_DRAW(2), O_DISCARD_HAND(2)
    # But opcodes in compiled json are flat lists.
    # We look for sequence: [10, 2, ..., 41, 2] (Draw=10, Discard=41)

    print("Searching for Rank 9 (Draw 2, Discard 2)...")
    found_rank9 = False
    for cid, card in member_db.items():
        # Check ability 0
        abs = card.get("abilities", [])
        if not abs:
            continue

        # We check the first ability's opcodes
        # compiled structure: abilities is list of dicts? or list of lists?
        # In compiled json, it's usually list of Ability structs
        # But let's check the structure in debug output.
        # "abilities": [ { "type": "Main", "opcodes": [...] } ]

        # We just search for simple text match first as it's easier
        name = card.get("name", "")
        text = card.get("text", "")
        original_text = card.get("original_text", "")

        # Rank 9: Draw 2, Discard 2
        # Cards: card を 2枚引き、... 2枚捨てる
        if "2枚引" in original_text and "2枚" in original_text and "捨" in original_text:
            print(f"FOUND RANK 9 CANDIDATE: {cid} ({card.get('card_no')}) - {name}")
            found_rank9 = True
        elif "2枚" in original_text and "引" in original_text and "捨" in original_text:
            # Even broader
            print(f"FOUND RANK 9 BROAD MATCH: {cid} ({card.get('card_no')}) - {name}")

        # Rank 19: Hand reveal sum 10, 20, 30...
        if "10、20、30" in original_text:
            print(f"FOUND RANK 19 CANDIDATE: {cid} ({card.get('card_no')}) - {name}")

        # Rank 5: All Blades as Any Heart
        # Text: "全ての（剣）は任意の色の（ハート）として扱う" or similar
        if "全ての" in original_text and "ハートとして扱う" in original_text:
            print(f"FOUND RANK 5 CANDIDATE: {cid} ({card.get('card_no')}) - {name}")
        elif "ブレードハート" in original_text and "ハートとして扱う" in original_text:
            print(f"FOUND RANK 5 BROAD MATCH: {cid} ({card.get('card_no')}) - {name}")

        # Specific ID search (if we have guesses)
        if card.get("card_no") == "PL!HS-PR-010-PR":
            print(f"SEARCHED CARD NO FOUND: {cid} (PL!HS-PR-010-PR)")

    if not found_rank9:
        print("No exact text match for Rank 9. Searching opcodes...")
        # ... logic to search opcodes if needed ...


if __name__ == "__main__":
    find_cards()
