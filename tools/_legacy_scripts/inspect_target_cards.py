import json
import os

data_path = "data/cards_compiled.json"
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

members = data.get("member_db", {})
lives = data.get("live_db", {})

target_ids = [25, 1069, 384, 53]

print("--- Card Inspection ---")
for tid in target_ids:
    m = members.get(str(tid))
    if m:
        print(f"ID {tid}: [Member] {m.get('card_no')} - {m.get('name')}")
    else:
        l = lives.get(str(tid))
        if l:
            print(f"ID {tid}: [Live] {l.get('card_no')} - {l.get('name')}")
        else:
            print(f"ID {tid}: NOT FOUND")

# Check if these are in verified_card_pool.json
pool_path = "verified_card_pool.json"
if os.path.exists(pool_path):
    with open(pool_path, "r", encoding="utf-8") as f:
        pool = json.load(f)

    verified = pool.get("verified_abilities", [])
    print("\n--- Verified Check ---")
    for tid in target_ids:
        m = members.get(str(tid))
        if m:
            card_no = m.get("card_no")
            is_v = card_no in verified
            print(f"{card_no}: Verified={is_v}")
