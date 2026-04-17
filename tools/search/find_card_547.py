import json
import sys

# Ensure stdout handles UTF-8
sys.stdout.reconfigure(encoding="utf-8")

with open("data/cards.json", "r", encoding="utf-8") as f:
    d = json.load(f)

keys = sorted(d.keys())
members = [k for k in keys if d[k].get("type") == "メンバー"]

if len(members) > 547:
    target_key = members[547]
    card_data = d[target_key]
    print("Index 547 Details:")
    print(f"  Key:  {target_key}")
    print(f"  Name: {card_data.get('name')}")
    print(f"  Prod: {card_data.get('product')}")
else:
    print(f"Index 547 not found in member list (size: {len(members)})")
