import json

with open("data/cards_compiled.json", encoding="utf-8") as f:
    data = json.load(f)

print("--- Rank 5 Search ---")
for cid, card in data["member_db"].items():
    txt = card.get("original_text", "")
    if "必要ハートを確認する時" in txt or "ALLブレード" in txt:
        print(f"ID {cid}: {card.get('card_no')} - {card.get('name')} - {txt[:50]}")

print("\n--- Card 901 Hearts ---")
c901 = data["member_db"]["901"]
print(f"901: {c901['name']} - Hearts: {c901['hearts']}")

print("\n--- Searching for Purple Energy ---")
for i in range(901, 1000):
    sid = str(i)
    if sid in data["member_db"]:
        c = data["member_db"][sid]
        h = c.get("hearts", [0] * 7)
        if h[5] > 0:  # Purple
            print(f"ID {i}: {c['name']} - Hearts: {h}")

print("\n--- Searching for Red Energy ---")
for i in range(901, 1000):
    sid = str(i)
    if sid in data["member_db"]:
        c = data["member_db"][sid]
        h = c.get("hearts", [0] * 7)
        if h[1] > 0:  # Red
            print(f"ID {i}: {c['name']} - Hearts: {h}")

print("\n--- Searching for Blue Energy ---")
for i in range(901, 1000):
    sid = str(i)
    if sid in data["member_db"]:
        c = data["member_db"][sid]
        h = c.get("hearts", [0] * 7)
        if h[4] > 0:  # Blue
            print(f"ID {i}: {c['name']} - Hearts: {h}")
