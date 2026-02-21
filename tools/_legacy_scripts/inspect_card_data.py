import json

with open("data/cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

output = []
output.append("=== Rule Card PL!HS-PR-010-PR ===")
if "PL!HS-PR-010-PR" in cards:
    output.append(json.dumps(cards["PL!HS-PR-010-PR"], ensure_ascii=False, indent=2))
else:
    output.append("Not found")

output.append("\n=== Cards with icon_b_all ===")
count = 0
for cid, data in cards.items():
    if "icon_b_all" in str(data):
        output.append(f"[{cid}] found icon_b_all")
        output.append(json.dumps(data, ensure_ascii=False, indent=2))
        count += 1
        if count >= 3:
            break

with open("card_inspection.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))
