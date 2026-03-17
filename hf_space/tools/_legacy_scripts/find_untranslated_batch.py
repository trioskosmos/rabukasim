import json
from collections import Counter

# Load cards
with open("data/cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

# Load existing translations
with open("data/manual_translations_en.json", "r", encoding="utf-8") as f:
    translations = json.load(f)

untranslated = []
for cid, card in cards.items():
    text = card.get("ability")  # Correct key is 'ability'
    if text and text != "なし" and cid not in translations:
        # Check if it has a translation already in the card object (just in case)
        if not card.get("ability_text_en"):
            # Normalize for better grouping
            import re

            norm = re.sub(r"\{\{.*?\|(.*?)\}\}", r"\1", text)
            norm = re.sub(r"\{\{.*?\}\}", "", norm)
            norm = re.sub(r"[・、。：！\!？\?\s\(\)（）/]", "", norm)
            untranslated.append((text, cid, norm))

# Count frequencies of NORMALIZED text
text_counts = Counter([n for t, c, n in untranslated])

# Print top 30 most frequent untranslated texts
with open("tools/batch6_candidates.txt", "w", encoding="utf-8") as f:
    f.write(f"Total untranslated unique texts: {len(text_counts)}\n\n")
    # Sort by count descending
    for norm, count in text_counts.most_common():
        # Find one CID for this text
        sample = next((t, c) for t, c, n in untranslated if n == norm)
        f.write(f"[{count}] {sample[1]}\n{sample[0]}\n")
        f.write("-" * 40 + "\n")
print("Written candidates to tools/batch6_candidates.txt")
