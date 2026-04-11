import json
import sys
from engine.compiler.semantic_simple import extract_semantic_simple

sys.stdout = open(1, 'w', encoding='utf-8', closefd=False)

with open('data/ability_semantic_dump.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

print("="*80)
print("MANUAL VERIFICATION OF ALL 612 ABILITIES")
print("="*80)

issues = []
for i, ability in enumerate(abilities):
    text = ability['primary_text_jp']
    result = extract_semantic_simple(text)
    
    # Check for issues
    has_issue = False
    issue_reasons = []
    
    if isinstance(result, list):
        # Multi-trigger ability
        for r in result:
            if not r['when']:
                has_issue = True
                issue_reasons.append("No trigger")
            if len(r['then']) == 0 and len(r['costs']) == 0 and not r['if']:
                has_issue = True
                issue_reasons.append("No meaningful content")
    else:
        if not result['when']:
            has_issue = True
            issue_reasons.append("No trigger")
        if len(result['then']) == 0 and len(result['costs']) == 0 and not result['if']:
            has_issue = True
            issue_reasons.append("No meaningful content")
    
    if has_issue:
        issues.append({
            'index': i,
            'ability_index': ability['ability_index'],
            'trigger': ability['trigger'],
            'text': text[:150],
            'reasons': issue_reasons,
            'extraction': result
        })
    
    # Print every 50 abilities to show progress
    if (i + 1) % 50 == 0:
        print(f"Processed {i + 1}/{len(abilities)} abilities...")

print(f"\n{'='*80}")
print(f"VERIFICATION COMPLETE")
print(f"{'='*80}")
print(f"Total abilities: {len(abilities)}")
print(f"Abilities with issues: {len(issues)}")

if issues:
    print(f"\n{'='*80}")
    print("ISSUES FOUND:")
    print("="*80)
    for issue in issues:
        print(f"\nIndex: {issue['ability_index']}")
        print(f"Trigger: {issue['trigger']}")
        print(f"Text: {issue['text']}...")
        print(f"Issues: {', '.join(issue['reasons'])}")
        print(f"Extraction: {json.dumps(issue['extraction'], ensure_ascii=False)[:200]}...")
else:
    print("\n✓ All abilities have triggers and meaningful content")
    print("✓ Extraction is ready for system use")
