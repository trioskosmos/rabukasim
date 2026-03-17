import json
import os

path = "data/cards_compiled.json"
print(f"Checking {path}...")
if not os.path.exists(path):
    print("File not found!")
    exit(1)

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Keys: {list(data.keys())}")
if "live_db" in data:
    lives = data["live_db"]
    print(f"live_db size: {len(lives)}")
    print(f"First 5 keys: {list(lives.keys())[:5]}")
else:
    print("live_db missing!")

target_id = "277"
if "member_db" in data:
    if target_id in data["member_db"]:
        v = data["member_db"][target_id]
        print(f"Details for {target_id}:")
        print(json.dumps(v, indent=2, ensure_ascii=False))
