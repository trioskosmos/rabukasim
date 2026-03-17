import json
import os

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\cards_compiled.json"
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        print(f"Top level keys: {list(data.keys())}")

        mdb = data.get("member_db", {})
        ldb = data.get("live_db", {})

        for cid in ["134", "132", "561"]:
            card = mdb.get(cid) or ldb.get(cid)
            if card:
                print(f"Card {cid}: {card.get('name')}")
                ab = card.get("ability", {})
                print(f"  Ability: {ab.get('raw_text')}")
                print(f"  Bytecode: {ab.get('bytecode')}")
            else:
                print(f"Card {cid} not found in member_db or live_db")
else:
    print(f"File not found at {path}")
