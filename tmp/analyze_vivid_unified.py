
import json
import os
import sys

# Add project root to sys.path
PROJECT_ROOT = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.game.deck_utils import UnifiedDeckParser

def main():
    cards_path = os.path.join(PROJECT_ROOT, 'data', 'cards.json')
    if not os.path.exists(cards_path):
        print(f"Error: {cards_path} not found")
        return

    with open(cards_path, 'r', encoding='utf-8') as f:
        card_db = json.load(f)

    parser = UnifiedDeckParser(card_db)
    
    deck_path = os.path.join(PROJECT_ROOT, 'ai', 'decks2', 'vividworld.txt')
    with open(deck_path, 'r', encoding='utf-8') as f:
        content = f.read()

    results = parser.extract_from_content(content)
    if not results:
        print("No results found")
        return

    d = results[0]
    print(f"Deck Name: {d['name']}")
    print(f"Main Deck Size: {len(d['main'])}")
    print(f"Energy Deck Size: {len(d['energy'])}")
    print(f"Type Counts: {d['type_counts']}")
    
    # Check for unknowns
    main_deck = d['main']
    unknowns = []
    for cid in main_deck:
        cdata = parser.resolve_card(cid)
        if not cdata:
            unknowns.append(cid)
    
    print(f"Unknown Cards in Main: {len(set(unknowns))}")
    if unknowns:
        print(f"First 10 Unknowns: {list(set(unknowns))[:10]}")

    # Check mapping
    print(f"Normalized DB Size: {len(parser.normalized_db)}")
    
    # Test specific card from the file
    test_cid = "PL!-BP5-011-N"
    cdata = parser.resolve_card(test_cid)
    print(f"Test Resolve '{test_cid}': {bool(cdata)}")
    if not cdata:
        # Check if it exists in any of the databases in some other form
        found = False
        for db_name, db in card_db.items():
            if not isinstance(db, dict): continue
            for k, v in db.items():
                if isinstance(v, dict) and (v.get('card_no') == test_cid or v.get('card_id') == test_cid):
                    print(f"Found '{test_cid}' in '{db_name}' but normalize failed? Normalize: '{parser.normalize_code(test_cid)}'")
                    found = True
                    break
            if found: break
        if not found:
            print(f"'{test_cid}' NOT FOUND in any DB")

if __name__ == "__main__":
    main()
