import json

with open("engine/data/cards.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total keys: {len(data)}")
patterns = ["HS-bp1-027"]
for k, v in data.items():
    if "HS-bp1-027" in k:
        print(f"Key: {k}, Type: {v.get('type')}")
    if isinstance(v, dict) and "rare_list" in v:
        for r in v["rare_list"]:
            if "HS-bp1-027" in str(r.get("card_no", "")):
                print(f"Key: {k}, RareList variant: {r.get('card_no')}, Type: {v.get('type')}")
