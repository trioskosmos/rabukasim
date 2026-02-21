import json
import os

path = "engine/data/cards_compiled.json"
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        m = len(data.get("member_db", {}))
        l = len(data.get("live_db", {}))
        e = len(data.get("energy_db", {}))
        print(f"Members: {m}, Lives: {l}, Energy: {e}")
else:
    print("File not found")
