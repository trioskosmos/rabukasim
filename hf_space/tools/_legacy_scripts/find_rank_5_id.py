import json

with open("data/cards_compiled.json", encoding="utf-8") as f:
    d = json.load(f)
for cid, c in d["member_db"].items():
    if c["card_no"] == "PL!HS-PR-010-PR":
        print(f"ID {cid} found.")
