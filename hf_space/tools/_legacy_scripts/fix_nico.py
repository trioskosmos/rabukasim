import json
import os

path = r"c:\Users\trios\Desktop\loveca-copy\data\cards.json"
# The system path might be different, let's check current dir or use relative
if not os.path.exists(path):
    path = "data/cards.json"

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

count = 0
for key, card in data.items():
    if "PL!-pb1-018" in key:
        card["pseudocode"] = (
            "登場: [ALL_PLAYERS] SELECT_CARDS(zone=DISCARD, cost<=2) -> PLAY_MEMBER(zone=DISCARD, state=WAIT)"
        )
        count += 1
        print(f"Updated {key}")

if count > 0:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Successfully updated {count} cards.")
else:
    print("No cards found.")
