#!/usr/bin/env python3
"""
Comprehensive analysis to find patterns/clauses with 133, 126, 124 matches.
"""

import json
from pathlib import Path
from collections import Counter

# Load abilities_extracted.json
data_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\abilities_extracted.json")
with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Searching for counts of 133, 126, 124...")
print("=" * 60)

# Search through all numeric values in the data
target_counts = [133, 126, 124]

def find_counts(obj, path=""):
    results = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            results.extend(find_counts(value, f"{path}.{key}" if path else key))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            results.extend(find_counts(item, f"{path}[{i}]"))
    elif isinstance(obj, int):
        if obj in target_counts:
            results.append((path, obj))
    return results

matches = find_counts(data)
print(f"\nFound {len(matches)} locations with target counts:")
for path, count in matches:
    print(f"  {count} at: {path}")

# Check the analysis section more thoroughly
if 'analysis' in data:
    analysis = data['analysis']
    print("\n\nAnalysis section keys:")
    for key in analysis.keys():
        print(f"  - {key}")

    # Check replacement_totals
    if 'replacement_totals' in analysis:
        print("\nReplacement totals:")
        for key, value in analysis['replacement_totals'].items():
            print(f"  {key}: {value}")

# Check if there's a pattern_variables section with specific counts
print("\n\nSearching for pattern_variables...")
def find_pattern_variables(obj, path=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if 'pattern_variables' in key.lower():
                print(f"Found pattern_variables at: {path}.{key}")
                if isinstance(value, dict):
                    for pk, pv in value.items():
                        if isinstance(pv, (int, list)):
                            if isinstance(pv, int) and pv in target_counts:
                                print(f"  {pk}: {pv} *** TARGET ***")
                            elif isinstance(pv, list):
                                print(f"  {pk}: list with {len(pv)} items")
                                if len(pv) in target_counts:
                                    print(f"    *** TARGET COUNT ***")
            find_pattern_variables(value, f"{path}.{key}" if path else key)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_pattern_variables(item, f"{path}[{i}]")

find_pattern_variables(data)
