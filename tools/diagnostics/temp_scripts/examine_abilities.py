#!/usr/bin/env python3
"""Examine ability text vs logic to identify needed changes."""

import json

with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("ABILITY TEXT vs LOGIC EXAMINATION")
print("=" * 80)

# Sample different ability types
categories = {
    'draw_effects': [],
    'discard_effects': [],
    'score_modifiers': [],
    'complex_conditions': [],
    'optional_costs': [],
    'baton_touch': [],
    'multi_part': []
}

for ability in data['abilities']:
    source = ability['source_ability_texts'][0]
    logic = source['logic']
    jp = source['jp']
    cards = source['cards']
    card = cards[0] if cards else 'UNKNOWN'
    
    entry = {
        'card': card,
        'jp': jp[:150],
        'logic': logic[:150],
        'trigger': ability['trigger']
    }
    
    # Categorize
    if 'draw' in logic:
        categories['draw_effects'].append(entry)
    elif 'discard' in logic:
        categories['discard_effects'].append(entry)
    
    if '+' in jp or '-' in jp:
        categories['score_modifiers'].append(entry)
    
    if 'if' in logic and logic.count('if') > 1:
        categories['complex_conditions'].append(entry)
    
    if 'optional' in logic and ('pay' in logic or 'discard' in logic):
        categories['optional_costs'].append(entry)
    
    if 'baton' in logic.lower():
        categories['baton_touch'].append(entry)
    
    if logic.count('\n') >= 3:
        categories['multi_part'].append(entry)
    
    # Limit each category
    for cat in categories:
        if len(categories[cat]) > 5:
            break

# Display by category
for cat_name, items in categories.items():
    if not items:
        continue
    
    print(f"\n{'=' * 80}")
    print(f"CATEGORY: {cat_name.upper().replace('_', ' ')} ({len(items)} shown)")
    print(f"{'=' * 80}")
    
    for i, item in enumerate(items[:3], 1):
        print(f"\n{i}. {item['card']} [Trigger: {item['trigger']}]")
        print(f"   JP: {item['jp']}...")
        print(f"   LOGIC: {item['logic']}...")
        
        # Analysis
        issues = []
        if 'score' in item['jp'].lower() and 'score' not in item['logic'].lower():
            issues.append("Score mentioned in JP but not in logic")
        if '+' in item['jp'] and '+' not in item['logic']:
            issues.append("+ modifier in JP but not logic")
        if '-' in item['jp'] and '-' not in item['logic']:
            issues.append("- modifier in JP but not logic")
        if 'cost' in item['jp'].lower() and 'cost' not in item['logic'].lower():
            issues.append("Cost mentioned in JP but not in logic")
        
        if issues:
            print(f"   [!] ISSUES: {', '.join(issues)}")
        else:
            print(f"   [OK] Looks correct")
        print("-" * 80)

print("\n" + "=" * 80)
print("SUMMARY OF POTENTIAL ISSUES")
print("=" * 80)

# Check for common missing patterns
all_issues = []
for ability in data['abilities'][:100]:
    source = ability['source_ability_texts'][0]
    logic = source['logic']
    jp = source['jp']
    
    # Score modifications
    if any(x in jp for x in ['スコア', 'score']) and 'score' not in logic.lower():
        all_issues.append(('score_not_extracted', jp[:60]))
    
    # Cost comparisons
    if 'コスト' in jp and 'cost' not in logic.lower():
        all_issues.append(('cost_not_extracted', jp[:60]))
    
    # Heart transformations
    if any(x in jp for x in ['ハートを', 'hearts']) and 'heart' not in logic.lower():
        all_issues.append(('hearts_not_extracted', jp[:60]))

# Count issues
issue_counts = {}
for issue_type, _ in all_issues:
    issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

print("\nCommon extraction gaps (from first 100 abilities):")
for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {count}x {issue_type}")

print(f"\n{'=' * 80}")
