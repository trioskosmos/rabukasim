import json

with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
    d = json.load(f)

# Find SD1-007
for k, v in d["member_db"].items():
    if v["card_no"] == "PL!-sd1-007-SD":
        ab = v["abilities"][0]
        print(f"SD1-007 (ID {k}):")
        print(f"  Trigger: {ab['trigger']}")
        print(f"  Conditions: {len(ab['conditions'])}")
        for j, c in enumerate(ab["conditions"]):
            print(f"    Cond {j}: type={c['type']}")
        print(f"  Effects: {len(ab['effects'])}")
        for j, e in enumerate(ab["effects"]):
            print(f"    Eff {j}: type={e['effect_type']}, val={e['value']}")
        break

# Find SD1-008
for k, v in d["member_db"].items():
    if v["card_no"] == "PL!-sd1-008-SD":
        ab = v["abilities"][0]
        print(f"SD1-008 (ID {k}):")
        print(f"  Trigger: {ab['trigger']}")
        print(f"  Conditions: {len(ab['conditions'])}")
        for j, c in enumerate(ab["conditions"]):
            print(f"    Cond {j}: type={c['type']}")
        print(f"  Effects: {len(ab['effects'])}")
        for j, e in enumerate(ab["effects"]):
            print(f"    Eff {j}: type={e['effect_type']}, val={e['value']}")
        break
