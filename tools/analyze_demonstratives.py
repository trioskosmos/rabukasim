#!/usr/bin/env python3
"""
Analyze patterns for optional demonstrative opportunities.
Identify entity patterns that could benefit from (?:この|その)? flexibility.
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
    dsl_patterns = eval(patterns_str)
else:
    print("Could not find DSL_PATTERNS")
    dsl_patterns = []

print("=" * 80)
print("DEMONSTRATIVE ANALYSIS")
print("=" * 80)

# Entity-related keywords that could benefit from optional demonstratives
entity_keywords = ['メンバー', 'カード', 'エネルギー', 'ハート', 'ブレード', 'ステージ', '手札', 'デッキ', '控え室']
demonstratives = ['この', 'その', 'あの']

# Analyze patterns for demonstrative opportunities
demonstrative_opportunities = []

for pattern in dsl_patterns:
    name = pattern['name']
    regex = pattern['regex']
    template = pattern['template']
    
    # Check if pattern contains entity keywords
    has_entity = any(keyword in regex or keyword in template for keyword in entity_keywords)
    
    # Check if pattern already has demonstratives
    has_demonstrative = any(demo in regex or demo in template for demo in demonstratives)
    
    if has_entity and not has_demonstrative:
        # Identify specific entity references in the regex
        entity_matches = []
        for keyword in entity_keywords:
            if keyword in regex:
                # Find the context around the entity keyword
                match = re.search(rf'([^。]{{0,20}}){keyword}([^。]{{0,20}})', regex)
                if match:
                    entity_matches.append({
                        'keyword': keyword,
                        'context': match.group(0)
                    })
        
        if entity_matches:
            demonstrative_opportunities.append({
                'name': name,
                'regex': regex,
                'template': template,
                'entity_matches': entity_matches
            })

print(f"\nPatterns with entity references lacking demonstratives: {len(demonstrative_opportunities)}")

# Sort by priority (patterns with multiple entity references first)
demonstrative_opportunities.sort(key=lambda x: len(x['entity_matches']), reverse=True)

print("\n" + "=" * 80)
print("TOP DEMONSTRATIVE OPPORTUNITIES")
print("=" * 80)

for i, pattern in enumerate(demonstrative_opportunities[:15]):
    print(f"\n--- Pattern {i+1}: {pattern['name']} ---")
    print(f"Entity references: {len(pattern['entity_matches'])}")
    for match in pattern['entity_matches']:
        print(f"  - {match['keyword']}: {match['context'][:60]}...")
    print(f"Current regex: {pattern['regex'][:80]}...")
    print(f"Suggested: Add (?:この|その)? before entity references")

print("\n" + "=" * 80)
print("IMPLEMENTATION RECOMMENDATIONS")
print("=" * 80)

recommendations = []

# Group patterns by entity type
entity_groups = defaultdict(list)
for pattern in demonstrative_opportunities:
    for match in pattern['entity_matches']:
        entity_groups[match['keyword']].append(pattern['name'])

for entity, patterns in sorted(entity_groups.items()):
    recommendations.append({
        'entity_type': entity,
        'pattern_count': len(patterns),
        'patterns': patterns[:5],
        'recommendation': f'Add (?:この|その)? before {entity} references in {len(patterns)} patterns'
    })

for rec in recommendations[:10]:
    print(f"\n{rec['entity_type']}:")
    print(f"  {rec['recommendation']}")
    print(f"  Patterns: {', '.join(rec['patterns'][:3])}{'...' if len(rec['patterns']) > 3 else ''}")

print(f"\nTotal demonstrative opportunities: {len(demonstrative_opportunities)}")
print(f"Entity types affected: {len(entity_groups)}")
