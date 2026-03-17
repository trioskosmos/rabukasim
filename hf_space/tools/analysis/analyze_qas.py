import collections
import json

try:
    with open("simplified_cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print("simplified_cards.json not found.")
    exit(1)

unique_qas = {}
qa_counts = collections.defaultdict(int)

unique_qas = collections.defaultdict(list)
total_entries = 0

for card in data:
    for qa in card.get("q_and_a", []):
        total_entries += 1
        title = qa.get("title", "Unknown")
        # Check if we already have this specific question text to avoid duplicates across cards
        existing = unique_qas[title]
        if not any(e["question"] == qa["question"] for e in existing):
            unique_qas[title].append(qa)

print(f"Total Q&A entries across all cards: {total_entries}")
print(f"Unique Q&A Titles: {len(unique_qas)}")

collision_count = 0
for title, items in unique_qas.items():
    if len(items) > 1:
        print(f"WARNING: Title '{title}' has {len(items)} variants!")
        collision_count += 1

print(f"Title Collisions: {collision_count}")
print("-" * 40)

sorted_titles = sorted(unique_qas.keys(), key=lambda x: int(x.split("（")[0].replace("Q", "")) if "Q" in x else 9999)

count = 0
for t in sorted_titles:
    for i, qa in enumerate(unique_qas[t]):
        suffix = f" (Variant {i + 1})" if len(unique_qas[t]) > 1 else ""
        print(f"{t}{suffix}: {qa['question'][:60].replace(chr(10), ' ')}...")
        count += 1
print(f"Total Unique Questions: {count}")
