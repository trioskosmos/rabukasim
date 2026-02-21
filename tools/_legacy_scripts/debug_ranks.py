import json

with open("data/cards_compiled.json", encoding="utf-8") as f:
    d = json.load(f)
for cid, c in d["member_db"].items():
    txt = c.get("original_text", "")
    if "として扱う" in txt:
        print(f"ID {cid}: {c['card_no']} - {c['name']} - {txt}")

print("\n--- CHECKING RANK 9 (ID 453) COST ---")
c9 = d["member_db"].get("453")
if c9:
    print(f"ID 453 Cost: {c9.get('cost')}")
    print(f"ID 453 Hearts: {c9.get('hearts')}")
