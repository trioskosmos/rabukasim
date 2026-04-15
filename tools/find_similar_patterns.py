#!/usr/bin/env python3
"""
Find similar patterns for consolidation opportunities.
Analyzes patterns for structural, regex, and semantic similarities.
"""

import json
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher

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
    dsl_patterns = eval(patterns_str)
else:
    print("Could not find DSL_PATTERNS")
    dsl_patterns = []

# Extract LITERAL_PATTERNS list
literal_match = re.search(r'LITERAL_PATTERNS\s*=\s*\[(.*?)\]\s*\n\s*FAMILY_PATTERNS', content, re.DOTALL)
if literal_match:
    literal_str = '[' + literal_match.group(1) + ']'
    literal_patterns = eval(literal_str)
else:
    print("Could not find LITERAL_PATTERNS")
    literal_patterns = []

# Extract FAMILY_PATTERNS list
family_match = re.search(r'FAMILY_PATTERNS\s*=\s*\[(.*?)\]\s*\n\nimport', content, re.DOTALL)
if family_match:
    family_str = '[' + family_match.group(1) + ']'
    family_patterns = eval(family_str)
else:
    print("Could not find FAMILY_PATTERNS")
    family_patterns = []

all_patterns = dsl_patterns + literal_patterns + family_patterns

print("=" * 80)
print("SIMILAR PATTERN ANALYSIS")
print("=" * 80)
print(f"Total patterns analyzed: {len(all_patterns)}")
print(f"  DSL patterns: {len(dsl_patterns)}")
print(f"  Literal patterns: {len(literal_patterns)}")
print(f"  Family patterns: {len(family_patterns)}")

def calculate_similarity(str1, str2):
    """Calculate similarity between two strings using SequenceMatcher."""
    return SequenceMatcher(None, str1, str2).ratio()

def extract_key_features(pattern):
    """Extract key features from pattern for comparison."""
    features = {
        'name': pattern.get('name', ''),
        'template': pattern.get('template', ''),
        'regex': pattern.get('regex', pattern.get('literal', '')),
        'structure': pattern.get('structure', ''),
    }
    
    # Extract template structure (remove variable placeholders)
    template_structure = re.sub(r'⟦[^⟧]+⟧', 'X', features['template'])
    features['template_structure'] = template_structure
    
    # Extract regex structure (remove character classes)
    regex_structure = re.sub(r'\[[^\]]+\]', 'X', features['regex'])
    regex_structure = re.sub(r'\\[^\\]', 'Y', regex_structure)
    features['regex_structure'] = regex_structure
    
    return features

# Analyze patterns for similarities
similar_groups = defaultdict(list)
similarity_threshold = 0.7  # 70% similarity threshold

print("\n" + "=" * 80)
print("TEMPLATE STRUCTURE SIMILARITY")
print("=" * 80)

for i, pattern1 in enumerate(all_patterns):
    features1 = extract_key_features(pattern1)
    
    for j, pattern2 in enumerate(all_patterns[i+1:], i+1):
        features2 = extract_key_features(pattern2)
        
        # Compare template structures
        template_sim = calculate_similarity(features1['template_structure'], features2['template_structure'])
        
        # Compare regex structures
        regex_sim = calculate_similarity(features1['regex_structure'], features2['regex_structure'])
        
        # Overall similarity
        overall_sim = (template_sim + regex_sim) / 2
        
        if overall_sim >= similarity_threshold:
            group_key = f"{features1['structure']}_{features2['structure']}"
            similar_groups[group_key].append({
                'pattern1': pattern1['name'],
                'pattern2': pattern2['name'],
                'template_sim': template_sim,
                'regex_sim': regex_sim,
                'overall_sim': overall_sim,
                'template1': features1['template'],
                'template2': features2['template'],
                'regex1': features1['regex'][:80] + '...' if len(features1['regex']) > 80 else features1['regex'],
                'regex2': features2['regex'][:80] + '...' if len(features2['regex']) > 80 else features2['regex'],
            })

print(f"\nFound {len(similar_groups)} pattern groups with {similarity_threshold*100}%+ similarity")

# Sort by similarity (highest first)
sorted_groups = sorted(similar_groups.values(), key=lambda x: max(item['overall_sim'] for item in x), reverse=True)

print("\n" + "=" * 80)
print("TOP SIMILAR PATTERN GROUPS")
print("=" * 80)

for i, group in enumerate(sorted_groups[:20]):
    if not group:
        continue
    
    best_match = max(group, key=lambda x: x['overall_sim'])
    print(f"\n--- Group {i+1} (Similarity: {best_match['overall_sim']*100:.1f}%) ---")
    print(f"Patterns: {[item['pattern1'] for item in group] + [item['pattern2'] for item in group]}")
    print(f"Template similarity: {best_match['template_sim']*100:.1f}%")
    print(f"Regex similarity: {best_match['regex_sim']*100:.1f}%")
    print(f"Example templates:")
    for item in group[:2]:
        print(f"  {item['pattern1']}: {item['template1'][:60]}...")
        print(f"  {item['pattern2']}: {item['template2'][:60]}...")

print("\n" + "=" * 80)
print("CONSOLIDATION RECOMMENDATIONS")
print("=" * 80)

recommendations = []

# Find patterns with identical structure but different parameters
structure_groups = defaultdict(list)
for pattern in all_patterns:
    structure = pattern.get('structure', '')
    if structure:
        structure_groups[structure].append(pattern['name'])

for structure, names in structure_groups.items():
    if len(names) > 2:
        recommendations.append({
            'category': 'Multiple patterns with identical structure',
            'structure': structure,
            'patterns': names,
            'count': len(names),
            'recommendation': f'Consolidate {len(names)} patterns with structure "{structure}" into flexible parameterized pattern'
        })

# Find patterns with very similar regex patterns
regex_groups = defaultdict(list)
for pattern in dsl_patterns:
    regex = pattern.get('regex', '')
    if regex:
        # Normalize regex for comparison
        normalized = re.sub(r'\\[^\\]', '', regex)
        normalized = re.sub(r'\[[^\]]+\]', 'X', normalized)
        regex_groups[normalized].append(pattern['name'])

for regex, names in regex_groups.items():
    if len(names) > 1:
        recommendations.append({
            'category': 'Very similar regex patterns',
            'regex_pattern': regex[:60] + '...',
            'patterns': names,
            'count': len(names),
            'recommendation': f'Merge {len(names)} patterns with similar regex into single flexible pattern'
        })

for rec in recommendations[:15]:
    print(f"\n{rec['category']}:")
    print(f"  {rec['recommendation']}")
    if 'structure' in rec:
        print(f"  Structure: {rec['structure']}")
    if 'regex_pattern' in rec:
        print(f"  Regex: {rec['regex_pattern']}")
    print(f"  Patterns ({rec['count']}): {', '.join(rec['patterns'][:5])}{'...' if len(rec['patterns']) > 5 else ''}")

print(f"\nTotal consolidation opportunities: {len(recommendations)}")
print(f"High-priority candidates (3+ similar patterns): {sum(1 for r in recommendations if r['count'] >= 3)}")
