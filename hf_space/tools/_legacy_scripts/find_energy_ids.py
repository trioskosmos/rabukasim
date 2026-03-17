import json

with open("data/cards_compiled.json", encoding="utf-8") as f:
    data = json.load(f)

print("Energy Cards:")
for i in range(901, 1000):
    sid = str(i)
    if sid in data["member_db"]:
        c = data["member_db"][sid]
        hearts = c.get("hearts", [0] * 7)
        # Pink=0, Red=1, Yellow=2, Green=3, Blue=4, Purple=5
        colors = []
        if hearts[0] > 0:
            colors.append("PINK")
        if hearts[1] > 0:
            colors.append("RED")
        if hearts[2] > 0:
            colors.append("YELLOW")
        if hearts[3] > 0:
            colors.append("GREEN")
        if hearts[4] > 0:
            colors.append("BLUE")
        if hearts[5] > 0:
            colors.append("PURPLE")

        if colors:
            print(f"ID {i}: {c['name']} - Hearts: {hearts} - Colors: {', '.join(colors)}")

print("\nSearching for Rank 5 card...")
for cid, card in data["member_db"].items():
    if "HS-PR-010" in card.get("card_no", ""):
        print(f"Rank 5 ID: {cid} - {card['card_no']} - {card['name']}")
