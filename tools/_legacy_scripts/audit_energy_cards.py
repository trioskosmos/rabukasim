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

print(f"Found {len(results)} energy-related cards.")
for r in results[:20]:
    print("-" * 20)
    print(f"Card: {r['card_no']}")
    print(f"Ability: {r['ability']}")
    print(f"Pseudocode: {r['pseudocode']}")
