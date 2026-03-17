#!/usr/bin/env python3
import json

with open("data/cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

card = cards.get("PL!N-bp1-069-P")
if card:
    print("Card Name:", card.get("name"))
    print("Card Unit:", card.get("unit"))
    print("Series:", card.get("series"))
    print("\nAbility Text:")
    print(card.get("ability", "No ability"))
    print("\nPseudocode:")
    print(card.get("pseudocode", "No pseudocode"))
else:
    print("Card not found!")
    # List all keys to find the correct one
    print("\nAvailable cards:")
    for k in list(cards.keys())[:10]:
        if cards[k].get("name") and "乙宗" in str(cards[k].get("name", "")):
            print(f"  {k}: {cards[k].get('name')}")
