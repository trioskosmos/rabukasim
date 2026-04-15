#!/usr/bin/env python3
"""
Analyze current patterns for specific improvements needed.
Focus on filler word additions and time notation optimizations.
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
print("SPECIFIC PATTERN IMPROVEMENT ANALYSIS")
print("=" * 80)
print(f"Total patterns to analyze: {len(patterns)}")

# Analyze patterns for specific issues
improvements = {
    'missing_demonstratives': [],
    'missing_player_refs': [],
    'time_notation_issues': [],
    'inflexible_card_types': [],
    'inflexible_zones': [],
    'consolidation_candidates': []
}

for pattern in patterns:
    name = pattern['name']
    regex = pattern['regex']
    template = pattern['template']
    
    # Check for missing demonstratives (この/その)
    if '([^。]+)' in regex and 'この' not in regex and 'その' not in regex:
        # Check if this pattern could benefit from optional demonstratives
        if any(word in template for word in ['MEMBER', 'CARD', 'ZONE', 'RESOURCE']):
            improvements['missing_demonstratives'].append({
                'name': name,
                'regex': regex,
                'template': template
            })
    
    # Check for missing player references (自分/相手)
    if '([^。]+)' in regex and '自分' not in regex and '相手' not in regex:
        if any(word in template for word in ['SOURCE', 'DESTINATION', 'PLAYER']):
            improvements['missing_player_refs'].append({
                'name': name,
                'regex': regex,
                'template': template
            })
    
    # Check time notation patterns
    if any(time in regex for time in ['ライブ終了時', 'ライブ開始時', 'ターン', '時']):
        improvements['time_notation_issues'].append({
            'name': name,
            'regex': regex,
            'template': template
        })
    
    # Check inflexible card types
    if 'メンバーカード' in regex or 'ライブカード' in regex or 'エネルギーカード' in regex:
        improvements['inflexible_card_types'].append({
            'name': name,
            'regex': regex,
            'template': template
        })
    
    # Check inflexible zones
    if 'ステージ' in regex and '([^。]+)' not in regex.split('ステージ')[0]:
        improvements['inflexible_zones'].append({
            'name': name,
            'regex': regex,
            'template': template
        })

print("\n" + "=" * 80)
print("PATTERNS NEEDING DEMONSTRATIVE FLEXIBILITY")
print("=" * 80)
print(f"Count: {len(improvements['missing_demonstratives'])}")
for item in improvements['missing_demonstratives'][:10]:
    print(f"\n{item['name']}:")
    print(f"  Regex: {item['regex'][:80]}...")
    print(f"  Template: {item['template']}")

print("\n" + "=" * 80)
print("PATTERNS NEEDING PLAYER REFERENCE FLEXIBILITY")
print("=" * 80)
print(f"Count: {len(improvements['missing_player_refs'])}")
for item in improvements['missing_player_refs'][:10]:
    print(f"\n{item['name']}:")
    print(f"  Regex: {item['regex'][:80]}...")
    print(f"  Template: {item['template']}")

print("\n" + "=" * 80)
print("TIME NOTATION PATTERNS")
print("=" * 80)
print(f"Count: {len(improvements['time_notation_issues'])}")
for item in improvements['time_notation_issues'][:15]:
    print(f"\n{item['name']}:")
    print(f"  Regex: {item['regex'][:80]}...")
    print(f"  Template: {item['template']}")

print("\n" + "=" * 80)
print("PATTERNS WITH INFLEXIBLE CARD TYPES")
print("=" * 80)
print(f"Count: {len(improvements['inflexible_card_types'])}")
for item in improvements['inflexible_card_types']:
    print(f"\n{item['name']}:")
    print(f"  Regex: {item['regex'][:80]}...")
    print(f"  Template: {item['template']}")

print("\n" + "=" * 80)
print("SPECIFIC IMPROVEMENT RECOMMENDATIONS")
print("=" * 80)

recommendations = []

# Time notation optimization
if improvements['time_notation_issues']:
    recommendations.append({
        'category': 'Time Notation Optimization',
        'issue': 'Multiple patterns handle time notations differently',
        'examples': [item['name'] for item in improvements['time_notation_issues'][:5]],
        'recommendation': 'Create unified time notation pattern: (?:ライブ(?:開始|終了)時|ターン\d+|時)?'
    })

# Card type flexibility
if improvements['inflexible_card_types']:
    recommendations.append({
        'category': 'Card Type Flexibility',
        'issue': 'Patterns hardcode specific card types instead of variables',
        'examples': [item['name'] for item in improvements['inflexible_card_types'][:5]],
        'recommendation': 'Replace hardcoded card types with ([^。]+(?:カード|ハート|ブレード))'
    })

# Demonstrative flexibility
if len(improvements['missing_demonstratives']) > 20:
    recommendations.append({
        'category': 'Demonstrative Flexibility',
        'issue': 'Many patterns lack optional demonstratives (この/その)',
        'examples': [item['name'] for item in improvements['missing_demonstratives'][:5]],
        'recommendation': 'Add optional (?:この|その)? before entity capture groups'
    })

for rec in recommendations:
    print(f"\n{rec['category']}:")
    print(f"  Issue: {rec['issue']}")
    print(f"  Examples: {', '.join(rec['examples'])}")
    print(f"  Recommendation: {rec['recommendation']}")

print("\n" + "=" * 80)
print("PRIORITY ACTIONS")
print("=" * 80)
print("""
1. HIGH PRIORITY: Fix inflexible card types (hardcoded メンバーカード/ライブカード)
2. HIGH PRIORITY: Optimize time notation patterns for consistency
3. MEDIUM PRIORITY: Add demonstrative flexibility to entity patterns
4. LOW PRIORITY: Add player reference flexibility where needed

These changes will make patterns more flexible and enable better clause recombination.
""")
