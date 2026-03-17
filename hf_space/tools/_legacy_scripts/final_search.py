import json

with open("data/cards_compiled.json", encoding="utf-8") as f:
    data = json.load(f)

print("--- PURPLE ENERGY SEARCH ---")
for i in range(901, 1500):
    sid = str(i)
    if sid in data["member_db"]:
        c = data["member_db"][sid]
        h = c.get("hearts", [0] * 7)
        if h[5] > 0:  # Purple index
            print(f"ID {i}: {c['name']} - Hearts: {h}")

print("\n--- RANK 5 SEARCH ---")
for cid, card in data["member_db"].items():
    txt = card.get("original_text", "")
    if "必要ハートを確認する時" in txt or "ALLブレード" in txt:
        print(f"RANK 5 ID: {cid} - {card.get('card_no')} - {card.get('name')} - {txt[:100]}")
