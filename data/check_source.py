#!/usr/bin/env python3
"""Check source cards.json."""
import json

with open('cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

print(f"Structure of cards.json: {type(cards)}")
if isinstance(cards, dict):
    print(f"Keys: {list(cards.keys())}")
    for key in list(cards.keys())[:5]:
        val = cards[key]
        print(f"  {key}: {type(val)}")
        if isinstance(val, list):
            print(f"    Length: {len(val)}")
            if val and isinstance(val[0], dict):
                print(f"    First item keys: {list(val[0].keys())[:5]}")
elif isinstance(cards, list):
    print(f"Length: {len(cards)}")
    if cards:
        print(f"First item type: {type(cards[0])}")
        if isinstance(cards[0], dict):
            print(f"First item keys: {list(cards[0].keys())[:5]}")
