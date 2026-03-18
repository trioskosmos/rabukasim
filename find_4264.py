#!/usr/bin/env python3
import json

with open("data/cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

# Search for cards by name
count = 0
for k, v in cards.items():
    if "名前" in k:
        continue
    name = v.get("name", "")
    if "乙宗" in str(name):
        print(f"Found: {k} - {name}")
        print(f"  Unit: {v.get('unit')}")
        print(f"  Ability: {v.get('ability', 'None')[:100]}")
        count += 1
        if count >= 3:
            break

if count == 0:
    print("No cards found with 乙宗 in name")
    # Try searching by ability text instead
    for k, v in list(cards.items())[:100]:
        if "4264" in k:
            print(f"\nFound by ID: {k}")
            print(json.dumps(v, ensure_ascii=False, indent=2)[:500])
