import json

with open("engine/data/cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

found = []
for cid, c in cards.items():
    ability = c.get("ability", "")
    if "1つを選ぶ" in ability and ("ハートを1つ得る" in ability or "ハートを得る" in ability):
        found.append((cid, ability))

for cid, ability in found:
    print(f"{cid}: {ability}\n")
