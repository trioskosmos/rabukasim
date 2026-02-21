import json
import os

with open("data/cards_compiled.json", encoding="utf-8") as f:
    data = json.load(f)

print("Searching for specific heart types...")
for i in range(901, 950):
    sid = str(i)
    if sid in data["member_db"]:
        c = data["member_db"][sid]
        hearts = c.get("hearts", [0] * 7)
        # Pink=0, Red=1, Yellow=2, Green=3, Blue=4, Purple=5
        colors = []
        if hearts[1] > 0 and "RED" not in colors:
            colors.append("RED")
        if hearts[4] > 0 and "BLUE" not in colors:
            colors.append("BLUE")
        if hearts[5] > 0 and "PURPLE" not in colors:
            colors.append("PURPLE")

        # We need specific cards that have Red, Blue, or Purple.
        if hearts[1] > 0 or hearts[4] > 0 or hearts[5] > 0:
            print(f"ID {i}: {c['name']} - Hearts: {hearts} - Colors: {', '.join(colors)}")
