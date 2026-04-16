#!/usr/bin/env python3
"""
Analyze remaining raw_text entries in simple effects extraction.
This script reads: data/simple_effects_extracted.json
This script writes: data/raw_effects_analysis.txt
"""

import json

with open('data/simple_effects_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find all raw_text entries
raw_entries = []
for item in data:
    if 'raw_text' in item['parsed']:
        raw_entries.append(item)

output = []
output.append("=" * 80)
output.append("RAW_TEXT ENTRIES ANALYSIS")
output.append("=" * 80)
output.append(f"Total entries: {len(data)}")
output.append(f"Raw_text entries: {len(raw_entries)}")
output.append(f"Percentage: {len(raw_entries) / len(data) * 100:.1f}%")
output.append("")

output.append("=" * 80)
output.append("ALL RAW_TEXT ENTRIES")
output.append("=" * 80)

for i, entry in enumerate(raw_entries, 1):
    output.append(f"\n[{i}] Costless: {entry['costless_text']}")
    output.append(f"    Triggers: {entry['triggers']}")
    output.append(f"    Card count: {entry['card_count']}")

with open('data/raw_effects_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Found {len(raw_entries)} raw_text entries")
print(f"Output written to data/raw_effects_analysis.txt")
