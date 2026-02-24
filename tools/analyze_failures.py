#!/usr/bin/env python3
"""Analyze failure patterns in COMPREHENSIVE_SEMANTIC_AUDIT.md"""

import re
from collections import defaultdict

def analyze_failures(report_path: str):
    """Parse the audit report and categorize failures."""
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse failure patterns
    failures = []
    for line in content.split('\n'):
        if '❌ FAIL' in line:
            # Extract card, ability, and error details
            match = re.search(r'\| ([^|]+) \| (Ab\d+) \| ❌ FAIL \| (.+) \|', line)
            if match:
                card = match.group(1).strip()
                ability = match.group(2).strip()
                details = match.group(3).strip()
                failures.append({
                    'card': card,
                    'ability': ability,
                    'details': details
                })
    
    # Categorize failures
    categories = defaultdict(list)
    
    for fail in failures:
        details = fail['details']
        
        # Extract the effect type and mismatch
        if 'COST: DISCARD_HAND' in details:
            categories['COST_DISCARD_HAND'].append(fail)
        elif 'COST: PAY_ENERGY' in details:
            categories['COST_PAY_ENERGY'].append(fail)
        elif 'COST: TAP_MEMBER' in details:
            categories['COST_TAP_MEMBER'].append(fail)
        elif 'EFFECT: BOOST_SCORE' in details:
            categories['EFFECT_BOOST_SCORE'].append(fail)
        elif 'EFFECT: DRAW' in details:
            categories['EFFECT_DRAW'].append(fail)
        elif 'EFFECT: ADD_BLADES' in details:
            categories['EFFECT_ADD_BLADES'].append(fail)
        elif 'EFFECT: ADD_HEARTS' in details:
            categories['EFFECT_ADD_HEARTS'].append(fail)
        elif 'EFFECT: TAP_OPPONENT' in details:
            categories['EFFECT_TAP_OPPONENT'].append(fail)
        elif 'EFFECT: RECOVER_MEMBER' in details:
            categories['EFFECT_RECOVER_MEMBER'].append(fail)
        elif 'EFFECT: RECOVER_LIVE' in details:
            categories['EFFECT_RECOVER_LIVE'].append(fail)
        elif 'EFFECT: LOOK_AND_CHOOSE' in details:
            categories['EFFECT_LOOK_AND_CHOOSE'].append(fail)
        elif 'EFFECT: MOVE_TO_DISCARD' in details:
            categories['EFFECT_MOVE_TO_DISCARD'].append(fail)
        elif 'EFFECT: MOVE_TO_DECK' in details:
            categories['EFFECT_MOVE_TO_DECK'].append(fail)
        elif 'DECK_SEARCH' in details:
            categories['DECK_SEARCH'].append(fail)
        else:
            categories['OTHER'].append(fail)
    
    # Print summary
    print("=" * 60)
    print("FAILURE ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"\nTotal Failures: {len(failures)}")
    print("\nBy Category:")
    print("-" * 40)
    
    for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"{cat}: {len(items)} failures")
    
    print("\n" + "=" * 60)
    print("DETAILED BREAKDOWN")
    print("=" * 60)
    
    for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"\n### {cat} ({len(items)} failures)")
        print("-" * 40)
        
        # Group by error pattern
        error_patterns = defaultdict(list)
        for item in items:
            # Extract expected vs got
            match = re.search(r'Exp (-?\d+), Got (-?\d+)', item['details'])
            if match:
                exp, got = match.group(1), match.group(2)
                pattern = f"Exp {exp}, Got {got}"
                error_patterns[pattern].append(item)
            else:
                error_patterns['Other'].append(item)
        
        for pattern, pattern_items in sorted(error_patterns.items(), key=lambda x: -len(x[1])):
            print(f"  {pattern}: {len(pattern_items)} cases")
            # Show first 3 examples
            for ex in pattern_items[:3]:
                print(f"    - {ex['card']} {ex['ability']}")
            if len(pattern_items) > 3:
                print(f"    ... and {len(pattern_items) - 3} more")

if __name__ == '__main__':
    analyze_failures('reports/COMPREHENSIVE_SEMANTIC_AUDIT.md')
