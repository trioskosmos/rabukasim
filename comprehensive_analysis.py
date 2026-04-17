"""Comprehensive analysis of parsing issues in abilities_extracted_from_cards.json"""

import json
from collections import defaultdict

def check_text_coverage(ability):
    """Check if all meaningful text is captured in the parsed structure."""
    issues = []
    
    full_text = ability.get('full_text', '')
    triggerless_text = ability.get('triggerless_text', '')
    costless_text = ability.get('costless_text', '')
    
    # Extract parsed text from structure
    parsed_parts = []
    
    # Add trigger
    triggers = ability.get('triggers')
    if triggers:
        parsed_parts.append(triggers)
    
    # Add use limit
    use_limit = ability.get('use_limit')
    if use_limit:
        parsed_parts.append(use_limit)
    
    # Add cost description
    cost = ability.get('cost')
    if cost and isinstance(cost, dict):
        # Cost should be captured in cost field
        pass
    
    # Add effect actions
    def extract_text_from_structure(obj, depth=0):
        if depth > 10:
            return
        if isinstance(obj, dict):
            if 'raw_text' in obj:
                parsed_parts.append(obj['raw_text'])
            if 'action' in obj:
                if isinstance(obj['action'], str):
                    parsed_parts.append(obj['action'])
                else:
                    extract_text_from_structure(obj['action'], depth + 1)
            for key, value in obj.items():
                if key not in ['raw_text', 'action']:
                    extract_text_from_structure(value, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                extract_text_from_structure(item, depth + 1)
    
    effect = ability.get('effect')
    if effect:
        extract_text_from_structure(effect)
    
    # Check for unparsed Japanese text patterns
    # These indicate text that should have been parsed but wasn't
    important_patterns = [
        '選ぶ',  # select/choose
        '支払う',  # pay
        'エネルギー',  # energy
        '枚',  # count counter
        '枚以上',  # count or more
        '枚以下',  # count or less
        '自分の',  # self's
        '相手の',  # opponent's
        'ステージ',  # stage
        '控え室',  # waitroom
        '手札',  # hand
        'デッキ',  # deck
        'エリア',  # area
        '移動',  # move
        '置く',  # place
        '得る',  # gain
        'ライブ',  # live
        'スコア',  # score
    ]
    
    # Check if important patterns in full_text are missing from parsed structure
    # This is a heuristic - not perfect but helps identify issues
    for pattern in important_patterns:
        if pattern in full_text:
            # Check if this pattern is captured
            captured = False
            for part in parsed_parts:
                if pattern in str(part):
                    captured = True
                    break
            if not captured:
                # This might be an issue, but not necessarily (could be in cost)
                if pattern not in ['枚', '枚以上', '枚以下']:  # These are too common
                    issues.append(f"Pattern '{pattern}' in text but may not be captured")
    
    return issues

def analyze_condition_structure(ability):
    """Analyze condition parsing."""
    issues = []
    
    def check_conditions(obj, path=""):
        if isinstance(obj, dict):
            if 'condition' in obj:
                condition = obj['condition']
                if isinstance(condition, dict):
                    if 'raw_text' in condition:
                        issues.append(f"Condition has raw_text at {path}")
                    if 'type' not in condition:
                        issues.append(f"Condition missing type at {path}")
            for key, value in obj.items():
                check_conditions(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_conditions(item, f"{path}[{i}]")
    
    effect = ability.get('effect')
    if effect:
        check_conditions(effect)
    
    return issues

def analyze_branch_structure(ability):
    """Analyze branch/conditional effect structure."""
    issues = []
    
    effect = ability.get('effect')
    if not effect:
        return issues
    
    def check_branches(obj, path=""):
        if isinstance(obj, dict):
            if 'branches' in obj:
                branches = obj['branches']
                if isinstance(branches, list):
                    for i, branch in enumerate(branches):
                        if not isinstance(branch, dict):
                            issues.append(f"Branch {i} at {path} is not a dict")
                        if 'cost_total' not in branch:
                            issues.append(f"Branch {i} at {path} missing cost_total")
                        if 'effect' not in branch:
                            issues.append(f"Branch {i} at {path} missing effect")
            for key, value in obj.items():
                check_branches(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_branches(item, f"{path}[{i}]")
    
    check_branches(effect)
    return issues

def analyze_cost_structure(ability):
    """Analyze cost parsing."""
    issues = []
    
    cost = ability.get('cost')
    if cost is None:
        return issues
    
    if not isinstance(cost, dict):
        issues.append("Cost is not a dict")
        return issues
    
    if 'type' not in cost:
        issues.append("Cost missing type")
    
    if cost.get('type') == 'move_cards':
        if 'source' not in cost:
            issues.append("Cost move_cards missing source")
        if 'destination' not in cost:
            issues.append("Cost move_cards missing destination")
        if 'count' not in cost:
            issues.append("Cost move_cards missing count")
    
    if cost.get('type') == 'reveal_cards':
        if 'source' not in cost:
            issues.append("Cost reveal_cards missing source")
        if 'count' not in cost:
            issues.append("Cost reveal_cards missing count")
    
    return issues

def analyze_effect_structure(ability):
    """Analyze effect parsing."""
    issues = []
    
    effect = ability.get('effect')
    if effect is None:
        if not ability.get('costless', True):
            issues.append("Effect is null but costless is False")
        return issues
    
    def check_actions(obj, path=""):
        if isinstance(obj, dict):
            if 'actions' in obj:
                actions = obj['actions']
                if isinstance(actions, list):
                    for i, action in enumerate(actions):
                        if not isinstance(action, dict):
                            issues.append(f"Action {i} at {path} is not a dict")
                        elif 'raw_text' in action:
                            issues.append(f"Action {i} has raw_text at {path}: {action['raw_text'][:50]}")
                        elif 'action' not in action:
                            issues.append(f"Action {i} missing action field at {path}")
            for key, value in obj.items():
                check_actions(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_actions(item, f"{path}[{i}]")
    
    check_actions(effect)
    return issues

def main():
    with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data['unique_abilities']
    
    all_issues = defaultdict(list)
    issue_counts = defaultdict(int)
    
    for i, ability in enumerate(abilities):
        issues = []
        issues.extend(check_text_coverage(ability))
        issues.extend(analyze_condition_structure(ability))
        issues.extend(analyze_branch_structure(ability))
        issues.extend(analyze_cost_structure(ability))
        issues.extend(analyze_effect_structure(ability))
        
        if issues:
            for issue in issues:
                all_issues[issue].append({
                    'index': i,
                    'card': ability.get('cards', ['Unknown'])[0] if ability.get('cards') else 'Unknown',
                    'full_text': ability.get('full_text', ''),
                    'ability': ability
                })
                issue_counts[issue] += 1
    
    print(f"Total abilities analyzed: {len(abilities)}")
    print(f"Abilities with issues: {len(all_issues)}")
    print(f"\nIssue summary:")
    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {count}: {issue}")
    
    # Save detailed report
    with open('comprehensive_parsing_report.txt', 'w', encoding='utf-8') as f:
        f.write("COMPREHENSIVE PARSING ISSUES REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total abilities analyzed: {len(abilities)}\n")
        f.write(f"Abilities with issues: {len(all_issues)}\n\n")
        
        f.write("ISSUE SUMMARY\n")
        f.write("-" * 80 + "\n")
        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{count}: {issue}\n")
        
        f.write("\n\nDETAILED ANALYSIS\n")
        f.write("=" * 80 + "\n\n")
        
        for issue, items in sorted(all_issues.items(), key=lambda x: len(x[1]), reverse=True):
            f.write(f"\n{issue} ({len(items)} occurrences):\n")
            f.write("-" * 80 + "\n")
            for item in items[:10]:  # Show first 10 examples
                f.write(f"\n[{item['index']}] {item['card']}\n")
                f.write(f"Full text: {item['ability'].get('full_text', '')}\n")
                f.write(f"Cost: {item['ability'].get('cost')}\n")
                f.write(f"Effect: {item['ability'].get('effect')}\n")
                f.write(f"\n")
    
    print("\nDetailed report saved to comprehensive_parsing_report.txt")

if __name__ == '__main__':
    main()
