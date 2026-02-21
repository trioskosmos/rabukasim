import json

with open("data/cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

energy_terms = ["エネルギー", "エネルギーデッキ"]
results = []

for k, v in cards.items():
    ability = v.get("ability", "")
    pseudocode = v.get("pseudocode", "")
    if any(term in ability for term in energy_terms):
        results.append({"card_no": k, "ability": ability, "pseudocode": pseudocode})

with open("reports/energy_audit.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print(f"Audit saved to reports/energy_audit.json. Total count: {len(results)}")
