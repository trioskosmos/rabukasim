"""Analyze all abilities for parsing quality."""
import json

def analyze_ability(ability, index):
    """Analyze a single ability and return notes."""
    notes = []
    issues = []
    
    full_text = ability.get('full_text', '')
    cost = ability.get('cost')
    effect = ability.get('effect')
    
    # Check for raw_text in cost
    if cost and isinstance(cost, str):
        issues.append(f"Cost is raw string: {cost}")
    
    if cost and isinstance(cost, dict) and 'raw_text' in cost:
        issues.append(f"Cost has raw_text: {cost['raw_text']}")
    
    # Check for raw_text in effect
    if effect and isinstance(effect, str):
        issues.append(f"Effect is raw string: {effect}")
    
    if effect and isinstance(effect, dict) and 'raw_text' in effect:
        issues.append(f"Effect has raw_text: {effect['raw_text']}")
    
    # Check for nested raw_text in actions
    if effect and isinstance(effect, dict) and 'actions' in effect:
        for i, action in enumerate(effect['actions']):
            if isinstance(action, dict) and 'raw_text' in action:
                issues.append(f"Action {i} has raw_text: {action['raw_text']}")
            if isinstance(action, dict) and 'action' in action and isinstance(action['action'], dict) and 'raw_text' in action['action']:
                issues.append(f"Action {i} nested action has raw_text: {action['action']['raw_text']}")
    
    # Check for missing cost or effect
    if not cost:
        issues.append("Missing cost")
    
    if not effect:
        issues.append("Missing effect")
    
    # Check for non-standard action types
    if effect and isinstance(effect, dict):
        def check_action_types(obj, path=""):
            if isinstance(obj, dict):
                if 'action' in obj:
                    action = obj['action']
                    if isinstance(action, str):
                        non_standard_actions = [
                            'choose_heart_cost', 'place_card', 'non_standard'
                        ]
                        if action in non_standard_actions:
                            notes.append(f"{path} has non-standard action: {action}")
                for key, value in obj.items():
                    check_action_types(value, f"{path}.{key}" if path else key)
        check_action_types(effect)
    
    # Check for missing optional flag on costs with "してもよい"
    if cost and isinstance(cost, dict) and 'してもよい' in full_text:
        if not cost.get('optional'):
            issues.append("Cost has 'してもよい' but missing optional flag")
    
    # Check for condition parsing
    if effect and isinstance(effect, dict) and 'condition' in effect:
        condition = effect['condition']
        if isinstance(condition, dict) and condition.get('type') == 'raw':
            issues.append(f"Condition is raw: {condition.get('text')}")
    
    return {
        'index': index,
        'full_text': full_text,
        'issues': issues,
        'notes': notes,
        'has_issues': len(issues) > 0
    }

def main():
    with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data['unique_abilities']
    
    results = []
    for i, ability in enumerate(abilities):
        result = analyze_ability(ability, i)
        results.append(result)
    
    # Summary
    total = len(results)
    with_issues = sum(1 for r in results if r['has_issues'])
    
    print(f"Total abilities: {total}")
    print(f"With issues: {with_issues}")
    print(f"Without issues: {total - with_issues}")
    print()
    
    # Detailed report
    for result in results:
        if result['has_issues']:
            print(f"Ability #{result['index']}:")
            print(f"  Text: {result['full_text'][:100]}...")
            for issue in result['issues']:
                print(f"  ISSUE: {issue}")
            for note in result['notes']:
                print(f"  NOTE: {note}")
            print()
    
    # Save detailed report
    with open('data/ability_analysis_report.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("Detailed report saved to data/ability_analysis_report.json")

if __name__ == '__main__':
    main()
