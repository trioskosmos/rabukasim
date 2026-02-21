import json

with open("data/cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

targets = []
for k, v in cards.items():
    if "ウェイト状態で置く" in v.get("ability", ""):
        targets.append(k)
        if "pseudocode" in v:
            pc = v["pseudocode"]
            if "ENERGY_CHARGE" in pc and "{wait=True}" not in pc:
                v["pseudocode"] = pc.replace("ENERGY_CHARGE(1)", "ENERGY_CHARGE(1) {wait=True}")
                print(f"Updated pseudocode for {k}")

with open("data/cards.json", "w", encoding="utf-8") as f:
    json.dump(cards, f, indent=4, ensure_ascii=False)

print(f"Found {len(targets)} cards with wait state energy charge.")
