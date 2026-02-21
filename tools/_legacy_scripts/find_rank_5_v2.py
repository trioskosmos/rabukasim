import json

with open("data/cards_compiled.json", encoding="utf-8") as f:
    d = json.load(f)
for cid, c in d["member_db"].items():
    if "好きな色" in c["original_text"] and "枚" not in c["original_text"]:
        print(f"ID {cid}: {c['card_no']} - {c['name']} - {c['original_text']}")
