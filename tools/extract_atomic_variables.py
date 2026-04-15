#!/usr/bin/env python3
"""
Extract atomic variables from extract_abilities_to_template.py
"""

import re
import sys
from collections import Counter

# Read the file
with open('extract_abilities_to_template.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all atomic variables (⟦...⟧ format)
matches = re.findall(r'⟦([^]]+)⟧', content)

# Count occurrences
counts = Counter(matches)

# Write results to file
with open('../data/atomic_variables_list.txt', 'w', encoding='utf-8') as f:
    f.write('Atomic variables found:\n')
    f.write(f'Total unique: {len(counts)}\n')
    f.write(f'Total occurrences: {sum(counts.values())}\n')
    f.write('\nUnique atomic variables and counts:\n')
    for var, count in sorted(counts.items(), key=lambda x: -x[1]):
        f.write(f'{var}: {count}\n')

print('Results written to atomic_variables_list.txt')
