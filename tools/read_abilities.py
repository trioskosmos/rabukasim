import json

with open("data/cards.json", "r", encoding="utf-8") as f:
    data = json.load(f)
for k in ["PL!S-PR-029-PR", "PL!S-PR-030-PR", "PL!S-PR-031-PR"]:
    if k in data:
        print(f"--- {k} ---")
        print(data[k].get("ability", ""))
