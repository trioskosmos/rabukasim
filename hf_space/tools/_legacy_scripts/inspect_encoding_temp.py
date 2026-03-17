import json

with open("engine/data/cards.json", "r", encoding="utf-8") as f:
    data = json.load(f)

card = data.get("PL!SP-sd1-002-SD")
if card:
    text = card.get("ability_text", "") or card.get("ability", "")
    print(f"Text repr: {repr(text)}")
    print(f"Has Liella? {'Liella' in text}")
    print(f"Has toujyou? {'toujyou' in text}")
    print("Hex:")
    print(" ".join("{:02x}".format(ord(c)) for c in text))
else:
    print("Card not found")
