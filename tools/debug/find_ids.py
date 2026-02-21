import json

with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    db = json.load(f)

members = {}
for cid, card in db["member_db"].items():
    if "sd1" in card["card_no"].lower():
        members[card["card_no"]] = (cid, card["cost"])

lives = {}
for cid, card in db["live_db"].items():
    if "sd1" in card["card_no"].lower():
        lives[card["card_no"]] = cid

print("Members (SD1):")
for no, info in sorted(members.items())[:10]:
    print(f"  {no}: ID {info[0]}, Cost {info[1]}")

print("\nLives (SD1):")
for no, cid in sorted(lives.items())[:10]:
    print(f"  {no}: ID {cid}")
