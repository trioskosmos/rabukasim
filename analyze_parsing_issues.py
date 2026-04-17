"""Analyze parsing issues in abilities_extracted_from_cards.json"""

import json
from collections import defaultdict

def analyze_ability(ability):
    """Analyze a single ability for parsing issues."""
    issues = []
    
    # Check if cost is present but costless is True
    if ability.get('cost') and ability.get('costless'):
        issues.append("Cost present but marked as costless")
    
    # Check if cost is null but costless is False
    if ability.get('cost') is None and not ability.get('costless', True):
        issues.append("Cost is null but costless is False")
    
    # Check if effect is null
    if ability.get('effect') is None:
        issues.append("Effect is null")
    
    # Check for raw_text in effect (unparsed)
    effect = ability.get('effect', {})
    if isinstance(effect, dict) and 'raw_text' in effect:
        issues.append(f"Effect has raw_text: {effect['raw_text'][:50]}...")
    
    # Check for nested raw_text in actions
    def check_raw(obj, path=""):
        if isinstance(obj, dict):
            if 'raw_text' in obj:
                issues.append(f"raw_text at {path}: {obj['raw_text'][:50]}...")
            for key, value in obj.items():
                check_raw(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_raw(item, f"{path}[{i}]")
    
    check_raw(effect)
    
    # Check if cost has type but no source/destination for move_cards
    cost = ability.get('cost', {})
    if isinstance(cost, dict):
        if cost.get('type') == 'move_cards':
            if 'source' not in cost:
                issues.append("Cost move_cards missing source")
            if 'destination' not in cost:
                issues.append("Cost move_cards missing destination")
    
    # Compare full_text with parsed structure
    full_text = ability.get('full_text', '')
    costless_text = ability.get('costless_text', '')
    
    # Check if costless_text is empty when there should be an effect
    if not costless_text and ability.get('effect'):
        issues.append("costless_text is empty but effect exists")
    
    # Check if costless_text is same as full_text when there should be a cost
    if costless_text == full_text and ability.get('cost') and not ability.get('costless'):
        issues.append("costless_text same as full_text but cost exists")
    
    return issues

def main():
    with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data['unique_abilities']
    
    all_issues = defaultdict(list)
    issue_counts = defaultdict(int)
    
    for i, ability in enumerate(abilities):
        issues = analyze_ability(ability)
        if issues:
            for issue in issues:
                all_issues[issue].append({
                    'index': i,
                    'card': ability.get('cards', ['Unknown'])[0] if ability.get('cards') else 'Unknown',
                    'full_text': ability.get('full_text', '')[:100],
                    'ability': ability
                })
                issue_counts[issue] += 1
    
    print(f"Total abilities analyzed: {len(abilities)}")
    print(f"Abilities with issues: {len([a for a in abilities if analyze_ability(a)])}")
    print(f"\nIssue summary:")
    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {count}: {issue}")
    
    print(f"\nDetailed examples for each issue:")
    for issue, items in all_issues.items():
        print(f"\n{issue} ({len(items)} occurrences):")
        for item in items[:3]:  # Show first 3 examples
            print(f"  [{item['index']}] {item['card']}")
            print(f"    Text: {item['full_text']}")
    
    # Save detailed report
    with open('parsing_issues_report.txt', 'w', encoding='utf-8') as f:
        f.write("PARSING ISSUES REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total abilities analyzed: {len(abilities)}\n")
        f.write(f"Abilities with issues: {len([a for a in abilities if analyze_ability(a)])}\n\n")
        
        f.write("ISSUE SUMMARY\n")
        f.write("-" * 80 + "\n")
        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{count}: {issue}\n")
        
        f.write("\n\nDETAILED EXAMPLES\n")
        f.write("=" * 80 + "\n\n")
        for issue, items in all_issues.items():
            f.write(f"\n{issue} ({len(items)} occurrences):\n")
            f.write("-" * 80 + "\n")
            for item in items[:5]:  # Show first 5 examples
                f.write(f"\n[{item['index']}] {item['card']}\n")
                f.write(f"Full text: {item['ability'].get('full_text', '')}\n")
                f.write(f"Cost: {item['ability'].get('cost')}\n")
                f.write(f"Effect: {item['ability'].get('effect')}\n")
    
    print("\nDetailed report saved to parsing_issues_report.txt")

if __name__ == '__main__':
    main()
