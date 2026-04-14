#!/usr/bin/env python3
"""
Analyze DSL patterns for consolidation opportunities.
This script identifies patterns that could be merged based on:
1. Similar regex structures
2. Low match counts (potential redundancy)
3. Similar templates/structures
"""

import json
import re
import sys
from collections import defaultdict

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load the pattern extraction script to get DSL_PATTERNS
import sys
sys.path.insert(0, 'c:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\tools')

# Import patterns from extract_abilities_to_template
with open('c:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\tools\\extract_abilities_to_template.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Extract DSL_PATTERNS list using regex
pattern_match = re.search(r'DSL_PATTERNS\s*=\s*\[(.*?)\]\s*\n\s*LITERAL_PATTERNS', content, re.DOTALL)
if pattern_match:
    patterns_str = '[' + pattern_match.group(1) + ']'
    patterns = eval(patterns_str)
else:
    print("Could not find DSL_PATTERNS")
    patterns = []

# Load pattern match counts from abilities_extracted.json
try:
    with open('c:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\data\\abilities_extracted_simple.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        abilities_data = data.get('abilities', [])
except:
    abilities_data = []

# Count pattern matches
pattern_counts = defaultdict(int)
pattern_examples = defaultdict(list)

for ability in abilities_data:
    for match in ability.get('pattern_matches', []):
        pattern_name = match['pattern_name']
        pattern_counts[pattern_name] += 1
        if len(pattern_examples[pattern_name]) < 3:
            pattern_examples[pattern_name].append(match['matched_text'][:100])

# Analyze patterns for consolidation opportunities
print("=" * 80)
print("PATTERN CONSOLIDATION ANALYSIS")
print("=" * 80)
print(f"\nTotal patterns: {len(patterns)}")
print(f"Patterns with matches: {len(pattern_counts)}")
print(f"Patterns without matches: {len(patterns) - len(pattern_counts)}")

print("\n" + "=" * 80)
print("PATTERNS WITH LOW MATCH COUNTS (Consolidation Candidates)")
print("=" * 80)
low_match_patterns = [(name, count) for name, count in pattern_counts.items() if count <= 3]
low_match_patterns.sort(key=lambda x: x[1])

for name, count in low_match_patterns[:20]:
    print(f"\n{name}: {count} matches")
    if pattern_examples[name]:
        print(f"  Examples: {pattern_examples[name]}")

print("\n" + "=" * 80)
print("PATTERNS WITHOUT MATCHES (Removal Candidates)")
print("=" * 80)
no_match_patterns = [p['name'] for p in patterns if p['name'] not in pattern_counts]
for name in no_match_patterns[:20]:
    print(f"  {name}")

print("\n" + "=" * 80)
print("SIMILAR STRUCTURE ANALYSIS")
print("=" * 80)

# Group patterns by structure
structure_groups = defaultdict(list)
for pattern in patterns:
    structure = pattern.get('structure', '')
    if structure:
        structure_groups[structure].append(pattern['name'])

# Find structures with multiple patterns
duplicate_structures = {s: names for s, names in structure_groups.items() if len(names) > 1}
print(f"\nStructures with multiple patterns: {len(duplicate_structures)}")

for structure, names in sorted(duplicate_structures.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
    print(f"\n{structure}: {len(names)} patterns")
    for name in names:
        count = pattern_counts.get(name, 0)
        print(f"  - {name} ({count} matches)")

print("\n" + "=" * 80)
print("REGEX SIMILARITY ANALYSIS")
print("=" * 80)

# Simple regex similarity based on common patterns
regex_patterns = []
for pattern in patterns:
    regex = pattern.get('regex', '')
    if regex:
        # Extract key regex features
        features = {
            'has_capture_groups': '(' in regex,
            'capture_group_count': regex.count('('),
            'has_word_boundary': r'\b' in regex,
            'has_optional': '?' in regex,
            'has_repetition': '*' in regex or '+' in regex,
            'has_character_class': '[' in regex,
            'length': len(regex)
        }
        regex_patterns.append((pattern['name'], features, regex))

# Find patterns with similar features
print("\nPatterns with similar capture group counts:")
capture_groups = defaultdict(list)
for name, features, regex in regex_patterns:
    capture_groups[features['capture_group_count']].append(name)

for count, names in sorted(capture_groups.items())[:10]:
    if len(names) > 5:
        print(f"\n{count} capture groups: {len(names)} patterns")
        for name in names[:10]:
            print(f"  - {name}")

print("\n" + "=" * 80)
print("CONSOLIDATION RECOMMENDATIONS")
print("=" * 80)

recommendations = []

# 1. Remove patterns with no matches
if no_match_patterns:
    recommendations.append(f"REMOVE: {len(no_match_patterns)} patterns with zero matches")

# 2. Consolidate patterns with same structure
for structure, names in duplicate_structures.items():
    if len(names) > 2:
        total_matches = sum(pattern_counts.get(name, 0) for name in names)
        if total_matches < 10:
            recommendations.append(f"CONSOLIDATE: {structure} - {len(names)} patterns with {total_matches} total matches")

# 3. Consolidate low-match patterns with similar structures
if len(low_match_patterns) > 10:
    recommendations.append(f"REVIEW: {len(low_match_patterns)} patterns with ≤3 matches each")

for rec in recommendations:
    print(f"\n{rec}")

print("\n" + "=" * 80)
print("DETAILED PATTERN LIST")
print("=" * 80)

for pattern in patterns:
    name = pattern['name']
    count = pattern_counts.get(name, 0)
    structure = pattern.get('structure', 'No structure')
    print(f"{name}: {count} matches | {structure}")
