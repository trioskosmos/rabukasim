#!/usr/bin/env python3
"""
Standardize time notation patterns across all affected patterns.
Identify patterns with inconsistent time handling and standardize them.
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

# Load the extract_abilities_to_template.py file
with open('c:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\tools\\extract_abilities_to_template.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract DSL_PATTERNS list
pattern_match = re.search(r'DSL_PATTERNS\s*=\s*\[(.*?)\]\s*\n\s*LITERAL_PATTERNS', content, re.DOTALL)
if pattern_match:
    patterns_str = '[' + pattern_match.group(1) + ']'
    patterns = eval(patterns_str)
else:
    print("Could not find DSL_PATTERNS")
    patterns = []

print("=" * 80)
print("TIME NOTATION STANDARDIZATION ANALYSIS")
print("=" * 80)

# Identify patterns with time notation issues
time_patterns = []
time_keywords = ['ライブ開始時', 'ライブ終了時', 'ターン', '時', '終了時']

for pattern in patterns:
    name = pattern['name']
    regex = pattern['regex']
    template = pattern['template']
    
    # Check if pattern contains time-related keywords
    has_time = any(keyword in regex or keyword in template for keyword in time_keywords)
    
    if has_time:
        time_patterns.append({
            'name': name,
            'regex': regex,
            'template': template,
            'time_keywords': [kw for kw in time_keywords if kw in regex or kw in template]
        })

print(f"\nPatterns with time notation: {len(time_patterns)}")

# Group patterns by time notation patterns
time_groups = defaultdict(list)

for pattern in time_patterns:
    # Extract time notation patterns from regex
    time_notations = []
    
    # Find common time patterns
    if 'ライブ開始時' in pattern['regex']:
        time_notations.append('ライブ開始時')
    if 'ライブ終了時' in pattern['regex']:
        time_notations.append('ライブ終了時')
    if re.search(r'ターン\d+', pattern['regex']):
        time_notations.append('ターンX')
    if '終了時まで' in pattern['regex']:
        time_notations.append('終了時まで')
    
    group_key = ','.join(sorted(set(time_notations)))
    time_groups[group_key].append(pattern['name'])

print(f"\nTime notation groups found: {len(time_groups)}")

for group, names in sorted(time_groups.items()):
    print(f"\nGroup '{group}': {len(names)} patterns")
    for name in names[:5]:
        print(f"  - {name}")
    if len(names) > 5:
        print(f"  ... and {len(names) - 5} more")

print("\n" + "=" * 80)
print("STANDARDIZATION RECOMMENDATIONS")
print("=" * 80)

recommendations = []

# Look for patterns that could use unified time notation
for pattern in time_patterns:
    name = pattern['name']
    regex = pattern['regex']
    template = pattern['template']
    
    # Check for hardcoded time patterns
    if 'ライブ開始時' in regex and 'ライブ終了時' not in regex:
        recommendations.append({
            'pattern': name,
            'issue': 'Only handles ライブ開始時, could be more flexible',
            'current': 'ライブ開始時 hardcoded',
            'suggested': 'Use (?:ライブ(?:開始|終了)時)? for flexibility'
        })
    
    if 'ライブ終了時' in regex and 'ライブ開始時' not in regex:
        recommendations.append({
            'pattern': name,
            'issue': 'Only handles ライブ終了時, could be more flexible',
            'current': 'ライブ終了時 hardcoded',
            'suggested': 'Use (?:ライブ(?:開始|終了)時)? for flexibility'
        })

print(f"\nStandardization opportunities: {len(recommendations)}")

for rec in recommendations[:15]:
    print(f"\n{rec['pattern']}:")
    print(f"  Issue: {rec['issue']}")
    print(f"  Current: {rec['current']}")
    print(f"  Suggested: {rec['suggested']}")

print("\n" + "=" * 80)
print("PRIORITY PATTERNS FOR STANDARDIZATION")
print("=" * 80)

# Find patterns with the most time variation
complex_time_patterns = []
for pattern in time_patterns:
    time_count = len(pattern['time_keywords'])
    if time_count >= 2:
        complex_time_patterns.append({
            'name': pattern['name'],
            'time_keywords': pattern['time_keywords'],
            'count': time_count
        })

complex_time_patterns.sort(key=lambda x: x['count'], reverse=True)

for pattern in complex_time_patterns[:10]:
    print(f"\n{pattern['name']} ({pattern['count']} time keywords):")
    print(f"  Time keywords: {', '.join(pattern['time_keywords'])}")
