import json
import os

try:
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db = json.load(f)
        print(f"940 in DB: {'940' in db['member_db']}")
        print(f"943 in DB: {'943' in db['member_db']}")
except Exception as e:
    print(f"Error reading DB: {e}")

print("Checking for engine_rust.pyd locations:")
for root, dirs, files in os.walk("."):
    if "engine_rust.pyd" in files:
        print(os.path.join(root, "engine_rust.pyd"))
