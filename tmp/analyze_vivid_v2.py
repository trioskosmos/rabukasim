
import json
import os
import sys

PROJECT_ROOT = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy'

def normalize_rust_style(code):
    if not code: return ""
    return code.replace('＋', "+").replace('－', "-").replace('ー', "-").strip().upper()

def main():
    cards_path = os.path.join(PROJECT_ROOT, 'data', 'cards.json')
    with open(cards_path, 'r', encoding='utf-8') as f:
        card_db = json.load(f)

    # Build a set of all normalized card_nos in the DB
    db_card_nos = set()
    for db_name in ['member_db', 'live_db', 'energy_db']:
        # Note: cards.json might have a different structure than what I expect
        pass
    
    # Actually, cards.json is a flat dict where keys are card_nos (or similar)
    for k, v in card_db.items():
        if isinstance(v, dict) and "card_no" in v:
            db_card_nos.add(normalize_rust_style(v["card_no"]))
    
    deck_path = os.path.join(PROJECT_ROOT, 'ai', 'decks2', 'vividworld.txt')
    with open(deck_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    found = 0
    missing = 0
    total_qty = 0
    found_qty = 0
    
    distinct_missing = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'): continue
        
        # Simple split for "ID x N"
        if ' x ' in line:
            parts = line.split(' x ')
            code = parts[0].strip()
            qty = int(parts[1].strip())
        else:
            code = line
            qty = 1
        
        total_qty += qty
        norm_code = normalize_rust_style(code)
        if norm_code in db_card_nos:
            found += 1
            found_qty += qty
        else:
            missing += 1
            distinct_missing.append(code)
            
    print(f"Total Lines: {found + missing}")
    print(f"Found Lines: {found}")
    print(f"Missing Lines: {missing}")
    print(f"Total Card Quantity: {total_qty}")
    print(f"Found Card Quantity: {found_qty}")
    print(f"Missing Card Quantity: {total_qty - found_qty}")
    
    if distinct_missing:
        print(f"First 10 Missing: {distinct_missing[:10]}")

if __name__ == "__main__":
    main()
