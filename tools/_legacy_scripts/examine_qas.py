import json

with open("simplified_cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

unique_qas = {}
for card in cards:
    for qa in card.get("q_and_a", []):
        if qa["title"] not in unique_qas:
            unique_qas[qa["title"]] = qa

sorted_titles = sorted(unique_qas.keys(), key=lambda x: int(x.split("Q")[1].split("（")[0]) if "Q" in x else 9999)

for t in sorted_titles[:20]:  # Look at first 20
    qa = unique_qas[t]
    print(f"--- {t} ---")
    print(f"PCODE: {qa.get('pseudocode', '')}")
    print(f"Q: {qa.get('question', '')[:100]}...")
    print(f"A: {qa.get('answer', '')[:100]}...")
