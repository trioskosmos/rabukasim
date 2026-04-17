"""Filter real issues from ability analysis."""
import json

with open('data/ability_analysis_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

real_issues = [r for r in data if r['has_issues'] and not any('Missing cost' in i for i in r['issues'])]

print(f'Real issues (not missing cost): {len(real_issues)}')
print()

for r in real_issues:
    print(f"Ability #{r['index']}:")
    print(f"  Text: {r['full_text'][:100]}...")
    for issue in r['issues']:
        print(f"  ISSUE: {issue}")
    for note in r['notes']:
        print(f"  NOTE: {note}")
    print()
