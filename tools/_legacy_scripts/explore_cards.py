"""Explore cards.json to find test candidates"""

import json

with open("data/cards.json", encoding="utf-8") as f:
    cards = json.load(f)

members = [(k, v) for k, v in cards.items() if v.get("type") == "メンバー" and v.get("ability")]
print(f"Found {len(members)} members with abilities\n")

# Find simple, testable abilities
for k, v in members[:10]:
    ability = v.get("ability", "")
    faq = v.get("faq", [])
    print(f"=== {k}: {v['name']} ===")
    print(f"Ability: {ability[:200]}")
    if faq:
        print(f"FAQ: {faq[0].get('answer', '')[:100]}...")
    print()
