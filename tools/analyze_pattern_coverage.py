#!/usr/bin/env python3
"""
Analyze which DSL_PATTERNS are actually matching the extracted abilities.
"""

import json
import re
import sys

# Import DSL_PATTERNS from the file
sys.path.insert(0, 'tools')
from extract_abilities_to_template import DSL_PATTERNS

# Load the extracted abilities
with open('data/abilities_extracted.json', encoding='utf-8') as f:
    abilities = json.load(f)

# Analyze which patterns match
pattern_matches = {}
unmatched_clauses = []

for ability in abilities:
    for clause in ability['clauses']:
        matched = False
        for pattern in DSL_PATTERNS:
            try:
                if re.search(pattern['regex'], clause):
                    matched = True
                    pattern_name = pattern['name']
                    if pattern_name not in pattern_matches:
                        pattern_matches[pattern_name] = 0
                    pattern_matches[pattern_name] += 1
                    break
            except re.error as e:
                print(f"Regex error in pattern {pattern['name']}: {e}")
        if not matched:
            unmatched_clauses.append(clause)

# Write analysis
with open('pattern_coverage.txt', 'w', encoding='utf-8') as f:
    f.write("PATTERN COVERAGE ANALYSIS\n")
    f.write("=" * 50 + "\n\n")
    
    f.write(f"Total abilities: {len(abilities)}\n")
    f.write(f"Total clauses: {sum(len(a['clauses']) for a in abilities)}\n")
    f.write(f"Matched patterns: {len(pattern_matches)}\n")
    f.write(f"Unmatched clauses: {len(unmatched_clauses)}\n\n")
    
    f.write("PATTERN MATCHES (sorted by frequency):\n")
    f.write("-" * 50 + "\n")
    for pattern_name, count in sorted(pattern_matches.items(), key=lambda x: -x[1]):
        f.write(f"{pattern_name}: {count}\n")
    
    f.write("\n\nUNMATCHED CLAUSES (first 20):\n")
    f.write("-" * 50 + "\n")
    for clause in unmatched_clauses[:20]:
        f.write(f"  {clause}\n")
    
    if len(unmatched_clauses) > 20:
        f.write(f"  ... and {len(unmatched_clauses) - 20} more\n")

print("Pattern coverage analysis written to pattern_coverage.txt")
