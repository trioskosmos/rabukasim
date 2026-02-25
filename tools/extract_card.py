
import json

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\cards_compiled.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

for cid, card in data.items():
    if card.get("card_no") == "PL!-sd1-007-SD":
        print(json.dumps(card, indent=2))
        break
else:
    print("Card not found")
