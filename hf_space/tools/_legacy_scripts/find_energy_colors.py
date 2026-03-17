import json

with open("data/cards_compiled.json", encoding="utf-8") as f:
    data = json.load(f)

print("--- ENERGY SEARCH ---")
for cid, card in data["member_db"].items():
    if card.get("card_no", "").startswith("E-"):
        h = card.get("hearts", [0] * 7)
        # Red=1, Green=3, Blue=4, Purple=5
        if max(h) > 0:
            colors = []
            if h[1] > 0:
                colors.append(f"Red:{h[1]}")
            if h[3] > 0:
                colors.append(f"Green:{h[3]}")
            if h[4] > 0:
                colors.append(f"Blue:{h[4]}")
            if h[5] > 0:
                colors.append(f"Purple:{h[5]}")
            if colors:
                print(f"ID {cid}: {card.get('name')} - {', '.join(colors)}")
