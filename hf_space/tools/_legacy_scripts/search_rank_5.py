import json

with open("data/cards_compiled.json", encoding="utf-8") as f:
    d = json.load(f)
print("--- SEARCH RESULTS ---")
for cid, c in d["member_db"].items():
    txt = c.get("original_text", "")
    if "1個を" in txt and "好きな色" in txt and "ハート1個として扱う" in txt:
        print(f"ID {cid}: {c['card_no']} - {c['name']} - {txt}")
