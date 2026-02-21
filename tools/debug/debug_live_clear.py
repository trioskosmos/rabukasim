import json

db = json.load(open("data/cards_compiled.json", "r", encoding="utf-8"))

# From game trace Turn 40:
stage_ids = ["53", "238", "91"]
live_ids = ["10023", "10011", "10023"]

print("=== STAGE HEARTS ===")
total = [0] * 7
for cid in stage_ids:
    m = db["member_db"].get(cid)
    if m:
        print(f"{cid}: {m['name']} Hearts={m['hearts']}")
        for i in range(7):
            total[i] += m["hearts"][i]
print(f"TOTAL STAGE HEARTS: {total}")

print("\n=== LIVE REQUIREMENTS ===")
combined = [0] * 7
for cid in live_ids:
    l = db["live_db"].get(cid)
    if l:
        print(f"{cid}: {l['name']} Req={l['required_hearts']}")
        for i in range(7):
            combined[i] += l["required_hearts"][i]
print(f"COMBINED LIVE REQ: {combined}")

print("\n=== CAN CLEAR? ===")
surplus = 0
for i in range(6):
    diff = total[i] - combined[i]
    if diff >= 0:
        surplus += diff
        print(f"Color {i}: Have {total[i]}, Need {combined[i]} -> OK (surplus {diff})")
    else:
        print(f"Color {i}: Have {total[i]}, Need {combined[i]} -> MISSING {abs(diff)}")

any_need = combined[6]
wildcards = total[6]
print(f"\nANY (STAR): Need {any_need}, Have Wildcards {wildcards}, Surplus from colors {surplus}")
print(f"Total available for ANY: {wildcards + surplus}")
if wildcards + surplus >= any_need:
    print("RESULT: CAN CLEAR ALL LIVES")
else:
    print(f"RESULT: CANNOT CLEAR - missing {any_need - wildcards - surplus} for ANY")
