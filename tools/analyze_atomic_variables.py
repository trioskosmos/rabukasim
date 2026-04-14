#!/usr/bin/env python3
"""
Properly analyze non-atomic variables and their connection to clauses.
This examines what variables actually contain and how they relate to game mechanics.
"""

import json
import sys
from collections import defaultdict

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load extracted abilities with variables
with open('c:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\data\\abilities_extracted_simple.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    abilities = data.get('abilities', [])

print("=" * 80)
print("ATOMIC VARIABLE ANALYSIS - Clause Connection Study")
print("=" * 80)

# Analyze extracted variables by pattern
pattern_variables = defaultdict(list)
for ability in abilities:
    for match in ability.get('pattern_matches', []):
        pattern_name = match['pattern_name']
        variables = match.get('extracted_variables', [])
        template = match.get('template', '')
        matched_text = match.get('matched_text', '')
        
        pattern_variables[pattern_name].append({
            'variables': variables,
            'template': template,
            'matched_text': matched_text
        })

print(f"\nTotal patterns analyzed: {len(pattern_variables)}")

# Analyze variable composition
variable_composition = defaultdict(int)
variable_examples = defaultdict(list)

for pattern_name, matches in pattern_variables.items():
    for match in matches[:5]:  # Limit to first 5 examples per pattern
        for var in match['variables']:
            # Analyze variable characteristics
            var_lower = var.lower()
            
            # Check for multi-word variables
            if ' ' in var or '}}' in var:
                variable_composition['multi_word'] += 1
                if len(variable_examples['multi_word']) < 10:
                    variable_examples['multi_word'].append(f"{pattern_name}: {var}")
            
            # Check for demonstratives
            if 'この' in var or 'その' in var or 'あの' in var:
                variable_composition['demonstrative'] += 1
                if len(variable_examples['demonstrative']) < 10:
                    variable_examples['demonstrative'].append(f"{pattern_name}: {var}")
            
            # Check for player references
            if '自分' in var or '相手' in var:
                variable_composition['player_reference'] += 1
                if len(variable_examples['player_reference']) < 10:
                    variable_examples['player_reference'].append(f"{pattern_name}: {var}")
            
            # Check for zone/location info
            if any(zone in var for zone in ['ステージ', '控え室', '手札', 'エネルギー', 'ライブカード']):
                variable_composition['zone_info'] += 1
                if len(variable_examples['zone_info']) < 10:
                    variable_examples['zone_info'].append(f"{pattern_name}: {var}")
            
            # Check for state info
            if any(state in var for state in ['アクティブ', 'ウェイト', '表', '裏']):
                variable_composition['state_info'] += 1
                if len(variable_examples['state_info']) < 10:
                    variable_examples['state_info'].append(f"{pattern_name}: {var}")
            
            # Check for timing/duration
            if any(time in var for time in ['ライブ終了', 'ターン', '時', 'まで']):
                variable_composition['timing_duration'] += 1
                if len(variable_examples['timing_duration']) < 10:
                    variable_examples['timing_duration'].append(f"{pattern_name}: {var}")
            
            # Check for pure game terms
            if any(term in var for term in ['メンバー', 'カード', 'ハート', 'ブレード', 'スコア']):
                variable_composition['game_term'] += 1
                if len(variable_examples['game_term']) < 10:
                    variable_examples['game_term'].append(f"{pattern_name}: {var}")

print("\n" + "=" * 80)
print("VARIABLE COMPOSITION ANALYSIS")
print("=" * 80)

for category, count in sorted(variable_composition.items(), key=lambda x: x[1], reverse=True):
    print(f"\n{category}: {count} occurrences")
    print(f"  Examples:")
    for example in variable_examples[category][:5]:
        print(f"    {example}")

print("\n" + "=" * 80)
print("DETAILED PATTERN VARIABLE ANALYSIS")
print("=" * 80)

# Show detailed analysis for high-frequency patterns
pattern_counts = {name: len(matches) for name, matches in pattern_variables.items()}
top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10]

for pattern_name, count in top_patterns:
    print(f"\n{pattern_name} ({count} matches):")
    matches = pattern_variables[pattern_name][:3]  # Show first 3 matches
    
    for i, match in enumerate(matches, 1):
        print(f"\n  Example {i}:")
        print(f"    Template: {match['template']}")
        print(f"    Matched: {match['matched_text'][:80]}...")
        print(f"    Variables: {match['variables']}")
        
        # Analyze each variable
        for var in match['variables']:
            analysis = []
            if 'この' in var or 'その' in var:
                analysis.append("demonstrative")
            if '自分' in var or '相手' in var:
                analysis.append("player_ref")
            if any(zone in var for zone in ['ステージ', '控え室', '手札']):
                analysis.append("zone")
            if any(term in var for term in ['メンバー', 'カード', 'ハート']):
                analysis.append("game_term")
            if ' ' in var or '}}' in var:
                analysis.append("multi_word")
            
            if analysis:
                print(f"      {var} -> {', '.join(analysis)}")

print("\n" + "=" * 80)
print("ATOMIC DECOMPOSITION RECOMMENDATIONS")
print("=" * 80)

recommendations = []

# Based on the analysis, provide specific recommendations
if variable_composition['demonstrative'] > 0:
    recommendations.append({
        'category': 'Demonstratives',
        'issue': 'Variables contain demonstratives (この/その) mixed with game terms',
        'example': variable_examples['demonstrative'][0] if variable_examples['demonstrative'] else None,
        'recommendation': 'Separate demonstratives from entity types: "このメンバー" → "この" + "メンバー"'
    })

if variable_composition['player_reference'] > 0:
    recommendations.append({
        'category': 'Player References',
        'issue': 'Variables contain player references (自分/相手) mixed with other info',
        'example': variable_examples['player_reference'][0] if variable_examples['player_reference'] else None,
        'recommendation': 'Separate player references from other components: "自分のステージ" → "自分" + "ステージ"'
    })

if variable_composition['multi_word'] > 0:
    recommendations.append({
        'category': 'Multi-word Variables',
        'issue': 'Variables contain multiple concepts in single capture',
        'example': variable_examples['multi_word'][0] if variable_examples['multi_word'] else None,
        'recommendation': 'Break down into atomic components based on clause structure'
    })

if variable_composition['timing_duration'] > 0:
    recommendations.append({
        'category': 'Timing/Duration',
        'issue': 'Timing and duration markers mixed with other concepts',
        'example': variable_examples['timing_duration'][0] if variable_examples['timing_duration'] else None,
        'recommendation': 'Separate timing conditions from actions: "ライブ終了時まで" → "ライブ終了時" + "まで"'
    })

for rec in recommendations:
    print(f"\n{rec['category']}:")
    print(f"  Issue: {rec['issue']}")
    if rec['example']:
        print(f"  Example: {rec['example']}")
    print(f"  Recommendation: {rec['recommendation']}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("""
Non-atomic variables are not just about filtering "filler words".
The issue is that patterns capture multi-component phrases that should be
broken down into atomic game mechanic components based on clause structure.

Key insights:
1. Demonstratives (この/その) serve a purpose - they specify which entity
2. Player references (自分/相手) are necessary for targeting
3. The problem is these are mixed with game terms in single variables
4. Variables should capture atomic components that can be recombined

Solution: Redesign patterns to capture atomic components separately,
then recombine them in templates for proper clause structure.
""")
