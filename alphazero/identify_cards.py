import json
from pathlib import Path

target_ids = [474, 410, 406, 12707, 420, 430, 459]
cards_compiled_path = Path("data/cards_compiled.json")

with open(cards_compiled_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"{'ID':<10} | {'No':<15} | {'Trig':<15} | {'Name':<20} | {'Pseudocode'}")
print("-" * 100)

for k, v in data.items():
    if not isinstance(v, dict):
        continue
    cid = v.get("card_id")
    if cid in target_ids:
        name = v.get("name", "Unknown")
        card_no = v.get("card_no", "Unknown")
        abilities = v.get("abilities", [])
        if abilities:
            for ab in abilities:
                pseudo = ab.get("pseudocode", "None")
                pseudo = pseudo.replace("\n", " ")[:60]
                trig = ab.get("trigger", "Unknown")
                print(f"{cid:<10} | {card_no:<15} | {trig:<15} | {name:<20} | {pseudo}")
        else:
            print(f"{cid:<10} | {card_no:<15} | {'None':<15} | {name:<20} | None")
