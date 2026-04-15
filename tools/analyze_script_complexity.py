#!/usr/bin/env python3
"""
Analyze extract_abilities_to_template.py for algorithmic complexity issues
and pattern consolidation opportunities.
"""

import re
import sys
from collections import defaultdict

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load the script
with open('c:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\tools\\extract_abilities_to_template.py', 'r', encoding='utf-8') as f:
    content = f.read()

print("=" * 80)
print("ALGORITHMIC COMPLEXITY ANALYSIS")
print("=" * 80)

# Find nested loops and potential O(n^2) issues
nested_loops = []
for i, line in enumerate(content.split('\n'), 1):
    if 'for ' in line.lower() and i > 1:
        # Check if previous lines also had for loops
        prev_lines = content.split('\n')[max(0, i-5):i]
        if any('for ' in prev_line.lower() for prev_line in prev_lines):
            nested_loops.append((i, line.strip()))

print(f"\nPOTENTIAL NESTED LOOPS (O(n^2) candidates): {len(nested_loops)}")
for line_num, line in nested_loops[:10]:
    print(f"  Line {line_num}: {line[:80]}...")

# Find pattern matching operations
pattern_operations = []
for i, line in enumerate(content.split('\n'), 1):
    if 're.search' in line or 're.match' in line or '.match(' in line or '.search(' in line:
        pattern_operations.append((i, line.strip()))

print(f"\nPATTERN MATCHING OPERATIONS: {len(pattern_operations)}")
for line_num, line in pattern_operations[:10]:
    print(f"  Line {line_num}: {line[:80]}...")

# Find list comprehensions and potential inefficiencies
list_comprehensions = []
for i, line in enumerate(content.split('\n'), 1):
    if '[' in line and 'for ' in line and 'in ' in line:
        list_comprehensions.append((i, line.strip()))

print(f"\nLIST COMPREHENSIONS (check for efficiency): {len(list_comprehensions)}")
for line_num, line in list_comprehensions[:10]:
    print(f"  Line {line_num}: {line[:80]}...")

# Find dictionary lookups in loops
dict_lookups = []
for i, line in enumerate(content.split('\n'), 1):
    if 'for ' in line.lower() and ('in ' in line or '[' in line):
        dict_lookups.append((i, line.strip()))

print(f"\nDICTIONARY/LOOKUP OPERATIONS IN LOOPS: {len(dict_lookups)}")
for line_num, line in dict_lookups[:10]:
    print(f"  Line {line_num}: {line[:80]}...")

print("\n" + "=" * 80)
print("PATTERN CONSOLIDATION OPPORTUNITITIES")
print("=" * 80)

# Extract DSL_PATTERNS to analyze for consolidation
pattern_match = re.search(r'DSL_PATTERNS\s*=\s*\[(.*?)\]\s*\n\s*LITERAL_PATTERNS', content, re.DOTALL)
if pattern_match:
    patterns_str = '[' + pattern_match.group(1) + ']'
    patterns = eval(patterns_str)
    
    # Analyze patterns for consolidation opportunities
    pattern_groups = defaultdict(list)
    
    for pattern in patterns:
        name = pattern['name']
        regex = pattern['regex']
        template = pattern['template']
        
        # Group by similar structure
        structure_key = template.replace('⟦', '').replace('⟧', '')
        pattern_groups[structure_key].append(name)
    
    # Find patterns with similar structures
    similar_structures = {k: v for k, v in pattern_groups.items() if len(v) > 1}
    
    print(f"\nPATTERNS WITH SIMILAR STRUCTURES: {len(similar_structures)}")
    for structure, names in sorted(similar_structures.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        print(f"\n  Structure: {structure[:60]}...")
        print(f"  Patterns ({len(names)}): {', '.join(names)}")
    
    # Analyze regex complexity
    complex_regexes = []
    for pattern in patterns:
        regex = pattern['regex']
        complexity_score = 0
        if '|' in regex: complexity_score += 1  # Alternation
        if '*' in regex: complexity_score += 1  # Kleene star
        if '+' in regex: complexity_score += 1  # Plus
        if '?' in regex: complexity_score += 1  # Optional
        if '[^' in regex: complexity_score += 1  # Negated character class
        if '(' in regex: complexity_score += regex.count('(')  # Capture groups
        
        if complexity_score > 5:
            complex_regexes.append((pattern['name'], regex, complexity_score))
    
    print(f"\nCOMPLEX REGEX PATTERNS (complexity score > 5): {len(complex_regexes)}")
    for name, regex, score in sorted(complex_regexes, key=lambda x: x[2], reverse=True)[:10]:
        print(f"  {name} (score: {score}): {regex[:60]}...")

print("\n" + "=" * 80)
print("PERFORMANCE OPTIMIZATION RECOMMENDATIONS")
print("=" * 80)

recommendations = []

if nested_loops:
    recommendations.append({
        'category': 'Nested Loops',
        'issue': f'Found {len(nested_loops)} potential nested loops',
        'optimization': 'Consider using sets/dicts for O(1) lookups instead of nested iterations',
        'priority': 'HIGH'
    })

if len(pattern_operations) > 50:
    recommendations.append({
        'category': 'Pattern Matching',
        'issue': f'Many pattern matching operations ({len(pattern_operations)})',
        'optimization': 'Consider compiling regex patterns once and reusing them',
        'priority': 'MEDIUM'
    })

if similar_structures:
    recommendations.append({
        'category': 'Pattern Consolidation',
        'issue': f'{len(similar_structures)} pattern groups have similar structures',
        'optimization': 'Consolidate similar patterns using more flexible regex with optional groups',
        'priority': 'HIGH'
    })

if complex_regexes:
    recommendations.append({
        'category': 'Regex Complexity',
        'issue': f'{len(complex_regexes)} complex regex patterns detected',
        'optimization': 'Simplify regex patterns or break them into smaller, more efficient patterns',
        'priority': 'MEDIUM'
    })

for rec in recommendations:
    print(f"\n{rec['category']} ({rec['priority']} PRIORITY):")
    print(f"  Issue: {rec['issue']}")
    print(f"  Optimization: {rec['optimization']}")

print("\n" + "=" * 80)
print("MANUAL INSPECTION REQUIRED")
print("=" * 80)
print("""
1. Check check_pattern_overlap() function - likely O(n^2) complexity
2. Review pattern matching loop in match_dsl_patterns() 
3. Examine coverage calculation logic for optimization
4. Look for redundant pattern matching operations
5. Consider using compiled regex patterns for performance
6. Review list/dict operations in loops for optimization opportunities
""")
