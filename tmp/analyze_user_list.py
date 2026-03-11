
import json
import os
import sys

# Add the project root to sys.path to import engine modules
sys.path.append(os.getcwd())

from engine.game.deck_utils import UnifiedDeckParser

def main():
    db_path = "data/cards.json"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found")
        return

    with open(db_path, "r", encoding="utf-8") as f:
        cards_raw = json.load(f)
    
    # UnifiedDeckParser expects { "member_db": {...}, "live_db": {...}, "energy_db": {...} }
    # But data/cards.json is a flat dict. Let's adapt it.
    card_db = {
        "member_db": {k: v for k, v in cards_raw.items() if v.get("type") == "メンバー"},
        "live_db": {k: v for k, v in cards_raw.items() if v.get("type") == "ライブ"},
        "energy_db": {k: v for k, v in cards_raw.items() if v.get("type") == "エネルギー"}
    }

    parser = UnifiedDeckParser(card_db)

    content = """
PL!-BP5-011-N x 4
PL!-PB1-024-N x 4
PL!HS-PR-022-PR x 2
PL!N-BP1-003-P x 3
PL!N-BP3-020-N x 1
PL!N-BP3-032-L x 2
PL!N-BP4-004-P x 2
PL!N-BP4-004-P+ x 1
PL!N-BP4-004-R+ x 1
PL!N-BP4-016-N x 4
PL!N-BP4-025-L x 3
PL!N-BP4-029-L x 3
PL!N-BP4-030-L x 4
PL!N-BP5-003-P x 2
PL!N-BP5-003-R x 1
PL!N-PB1-011-R x 2
PL!N-PB1-027-N x 4
PL!N-PB1-059-SRE x 1
PL!N-PB1-060-SRE x 1
PL!N-PB1-071-SRE x 1
PL!N-PB1-073-SRE x 1
PL!N-PB1-074-SRE x 1
PL!N-PB1-077-SRE x 1
PL!N-SD1-004-SD x 3
PL!N-SD1-006-SD x 4
PL!SP-PB1-014-N x 4
PL!SP-PB1-038-SRE x 1
PL!SP-PB1-039-SRE x 1
PL!SP-PB1-040-SRE x 1
PL!SP-PB1-041-SRE x 1
PL!SP-PB1-042-SRE x 1
PL!SP-PB1-043-SRE x 1
PL!SP-SD1-003-SD x 2
PL!SP-SD1-019-SD x 4
"""

    results = parser.extract_from_content(content)
    
    if not results:
        print("No results found.")
        return

    deck = results[0]
    print(f"Deck Name: {deck['name']}")
    print("-" * 40)
    print(f"Total Main cards: {len(deck['main'])}")
    print(f"Total Energy cards: {len(deck['energy'])}")
    print("-" * 40)
    print("Type Counts:")
    for k, v in deck['type_counts'].items():
        print(f"  {k}: {v}")
    
    print("-" * 40)
    print("Resolution Check:")
    unique_ids = set(deck['main'] + deck['energy'])
    resolved_count = 0
    missing = []
    for uid in unique_ids:
        cdata = parser.resolve_card(uid)
        if cdata:
            resolved_count += 1
        else:
            missing.append(uid)
    
    print(f"Resolved Unique IDs: {resolved_count} / {len(unique_ids)}")
    if missing:
        print("Missing IDs:")
        for m in missing:
            print(f"  - {m}")

if __name__ == "__main__":
    main()
