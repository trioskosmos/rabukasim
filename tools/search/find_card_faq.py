import json
import sys

# Ensure stdout handles UTF-8
sys.stdout.reconfigure(encoding="utf-8")

target_no = "PL!S-pb1-004-R"
found = False

with open("data/cards.json", "r", encoding="utf-8") as f:
    d = json.load(f)
    for k, v in d.items():
        if v.get("card_no") == target_no:
            print(json.dumps(v, indent=2, ensure_ascii=False))
            found = True
            break

if not found:
    print(f"Card {target_no} not found.")
