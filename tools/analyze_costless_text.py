#!/usr/bin/env python3
"""
Analyze costless_text field across all abilities.
This script reads: ../data/abilities_extracted_from_cards.json
This script writes: ../data/costless_text_analysis.txt
"""

import json
from collections import Counter

with open('../data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract all costless_text values
costless_texts = []
for ab in data['unique_abilities']:
    costless_text = ab.get('costless_text', '')
    if costless_text:
        costless_texts.append(costless_text)

# Group by trigger
by_trigger = {}
for ab in data['unique_abilities']:
    trigger = ab.get('triggers', 'None')
    costless_text = ab.get('costless_text', '')
    if trigger not in by_trigger:
        by_trigger[trigger] = []
    if costless_text:
        by_trigger[trigger].append(costless_text)

# Count unique costless_texts
unique_costless_texts = list(set(costless_texts))

output = []
output.append("=" * 80)
output.append("COSTLESS_TEXT ANALYSIS")
output.append("=" * 80)
output.append(f"Total abilities: {len(data['unique_abilities'])}")
output.append(f"Total costless_text entries: {len(costless_texts)}")
output.append(f"Unique costless_texts: {len(unique_costless_texts)}")
output.append("")

# Word/phrase frequency
all_words = []
for text in costless_texts:
    words = text.split()
    all_words.extend(words)

word_counts = Counter(all_words)
output.append("=" * 80)
output.append("TOP 20 MOST COMMON WORDS")
output.append("=" * 80)
for word, count in word_counts.most_common(20):
    output.append(f"{word}: {count}")

output.append("\n" + "=" * 80)
output.append("ALL UNIQUE COSTLESS_TEXTS")
output.append("=" * 80)
for i, text in enumerate(unique_costless_texts, 1):
    output.append(f"\n[{i}] {text}")

# Write to file
with open('../data/costless_text_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Analyzed {len(costless_texts)} costless_text entries")
print(f"Found {len(unique_costless_texts)} unique costless_texts")
print(f"Output written to ../data/costless_text_analysis.txt")
