import json
from collections import Counter

# Load the extracted abilities data
with open('data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Collect all non-atomic variables that need further decomposition
non_atomic_vars = []
pattern_usage = Counter()

for ability in data['dsl_pattern_analysis']['text_matches']:
    for match in ability['matches']:
        if 'decomposed_variables' in match and match['decomposed_variables']:
            for i, var_decomp in enumerate(match['decomposed_variables']):
                if not var_decomp.get('atomic'):
                    # This variable was decomposed further
                    if var_decomp.get('decomposition'):
                        for sub_decomp in var_decomp['decomposition']:
                            pattern_name = sub_decomp['match']['pattern_name']
                            pattern_usage[pattern_name] += 1
                else:
                    # This variable is atomic - check if it's actually long (might need decomposition)
                    if len(match['variables'][i]) > 15:
                        non_atomic_vars.append({
                            'variable': match['variables'][i],
                            'pattern': match['pattern_name'],
                            'ability': ability['original'][:80],
                        })

print("=== DECOMPOSITION ANALYSIS ===\n")
print(f"Total abilities: {len(data['dsl_pattern_analysis']['text_matches'])}")
print(f"Patterns used in recursive decomposition: {len(pattern_usage)}")
print(f"\n=== MOST USED PATTERNS IN RECURSIVE DECOMPOSITION ===")
for pattern, count in pattern_usage.most_common(20):
    print(f"  {pattern}: {count}")

print(f"\n=== VARIABLES MARKED ATOMIC BUT LENGTH > 15 (may need decomposition) ===")
print(f"Total: {len(non_atomic_vars)}")

# Group by length
length_groups = Counter()
for var in non_atomic_vars:
    length = len(var['variable'])
    length_groups[length] += 1

print(f"\n=== DISTRIBUTION BY LENGTH ===")
for length in sorted(length_groups.keys()):
    print(f"  Length {length}: {length_groups[length]} variables")

print(f"\n=== TOP 20 LONGEST VARIABLES MARKED ATOMIC ===")
sorted_vars = sorted(non_atomic_vars, key=lambda x: len(x['variable']), reverse=True)
for i, var in enumerate(sorted_vars[:20]):
    print(f"\n{i+1}. Length {len(var['variable'])}")
    print(f"   Variable: {var['variable'][:70]}...")
    print(f"   From pattern: {var['pattern']}")
    print(f"   Ability: {var['ability']}...")

# Analyze common patterns in these long variables
print(f"\n=== COMMON PATTERNS IN LONG ATOMIC VARIABLES ===")

# Check for common patterns
patterns_to_check = [
    ('icon', r'\{\{[^}]+\}\}'),
    ('duration', r'終了時まで'),
    ('zone', r'の([^。]+)に'),
    ('condition', r'場合'),
    ('action', r'を([^。]+)する'),
    ('number', r'\d+'),
]

import re
for pattern_name, pattern_regex in patterns_to_check:
    matches = 0
    for var in non_atomic_vars:
        if re.search(pattern_regex, var['variable']):
            matches += 1
    if matches > 0:
        print(f"  {pattern_name}: {matches}/{len(non_atomic_vars)} variables")
