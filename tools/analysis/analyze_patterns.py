import collections
import json

with open("simplified_cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

patterns = collections.defaultdict(int)
unique_qas = {}

for card in cards:
    for qa in card.get("q_and_a", []):
        pcode = qa.get("pseudocode", "")
        if pcode and qa["title"] not in unique_qas:
            unique_qas[qa["title"]] = qa
            # Extract RULING: categories
            if "RULING:" in pcode:
                cat_part = pcode.split("->")[0].replace("RULING:", "").strip()
                for cat in cat_part.split("|"):
                    patterns[cat.strip()] += 1
            else:
                patterns["NO_RULING_PREFIX"] += 1

print("Pseudocode Pattern Distribution:")
for cat, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
    print(f"{cat}: {count}")
