#!/usr/bin/env python3
"""
Categorize batontouch occurrences into distinct pattern variations.
"""

import json
from pathlib import Path
from collections import defaultdict

# Load abilities_extracted.json
extracted_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\abilities_extracted.json")
with open(extracted_file, 'r', encoding='utf-8') as f:
    extracted_data = json.load(f)

# Search for batontouch in extracted data
def search_batontouch(obj, path=""):
    results = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            results.extend(search_batontouch(value, f"{path}.{key}" if path else key))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            results.extend(search_batontouch(item, f"{path}[{i}]"))
    elif isinstance(obj, str):
        if 'バトンタッチ' in obj:
            results.append((path, obj))
    return results

batontouch_matches = search_batontouch(extracted_data)

# Categorize patterns
categories = defaultdict(list)

for path, text in batontouch_matches:
    # Skip residual candidates (these are fragments)
    if 'residual_candidates' in path:
        continue
    
    # Categorize based on pattern structure
    if 'コストが低い' in text or 'コスト(\d+)以下' in text:
        categories['cost_based_batontouch'].append((path, text))
    elif 'このターン中に' in text:
        categories['turn_based_batontouch'].append((path, text))
    elif 'バトンタッチで置けない' in text or 'バトンタッチで.*に置けない' in text:
        categories['batontouch_restriction'].append((path, text))
    elif 'バトンタッチして登場していないかぎり' in text:
        categories['negative_batontouch_condition'].append((path, text))
    elif 'バトンタッチして登場した場合' in text:
        categories['simple_batontouch'].append((path, text))
    else:
        categories['other_batontouch'].append((path, text))

# Output results
output_lines = []
output_lines.append("Batontouch Pattern Categorization")
output_lines.append("=" * 80)

for category, items in sorted(categories.items()):
    output_lines.append(f"\n{category}: {len(items)} occurrences")
    output_lines.append("-" * 40)
    
    # Extract unique patterns
    unique_patterns = set()
    for path, text in items:
        # Create a normalized version by replacing variables
        import re
        normalized = re.sub(r'\d+', 'N', text)
        normalized = re.sub(r'『[^』]+』', '『GROUP』', normalized)
        normalized = re.sub(r'「[^」]+」', '「GROUP」', normalized)
        normalized = re.sub(r'⟦[^⟧]+⟧', '⟦X⟧', normalized)
        unique_patterns.add(normalized)
    
    output_lines.append(f"  Unique patterns: {len(unique_patterns)}")
    for i, pattern in enumerate(sorted(unique_patterns)[:5]):
        output_lines.append(f"    {i+1}. {pattern[:100]}...")
    if len(unique_patterns) > 5:
        output_lines.append(f"    ... and {len(unique_patterns) - 5} more")

# Save to file
output_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\batontouch_categorization.txt")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print(f"Categorization saved to {output_file}")
for category, items in sorted(categories.items()):
    print(f"  {category}: {len(items)}")
