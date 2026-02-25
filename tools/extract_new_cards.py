#!/usr/bin/env python
"""Extract new cards from cards.json and update related files."""

import json
import os

def main():
    # Load cards
    with open('data/cards.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)
    
    with open('data/cards_old.json', 'r', encoding='utf-8') as f:
        old = json.load(f)
    
    new_ids = set(cards.keys()) - set(old.keys())
    print(f"Found {len(new_ids)} new cards")
    
    # Extract unique names and units from new cards
    names = set()
    units = set()
    series_set = set()
    
    for cid in new_ids:
        card = cards[cid]
        if 'name' in card and card['name']:
            names.add(card['name'])
        if 'unit' in card and card['unit']:
            units.add(card['unit'])
        if 'series' in card and card['series']:
            series_set.add(card['series'])
    
    print("\n=== New Names ===")
    for n in sorted(names):
        print(f"  {n}")
    
    print("\n=== New Units ===")
    for u in sorted(units):
        print(f"  {u}")
    
    print("\n=== New Series ===")
    for s in sorted(series_set):
        print(f"  {s}")
    
    # Save to a file for reference
    new_cards_info = {
        "count": len(new_ids),
        "card_ids": sorted(new_ids),
        "names": sorted(names),
        "units": sorted(units),
        "series": sorted(series_set)
    }
    
    with open('data/new_cards_info.json', 'w', encoding='utf-8') as f:
        json.dump(new_cards_info, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved new cards info to data/new_cards_info.json")

if __name__ == "__main__":
    main()
