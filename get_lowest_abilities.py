import json
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

data = json.load(open('data/abilities_extracted_simple.json', 'r', encoding='utf-8'))

# Get abilities below 70% coverage
below_70 = [a for a in data['abilities'] if a['coverage'] < 0.7]
below_70.sort(key=lambda x: x['coverage'])

print(f"Top 10 abilities with lowest coverage:")
print("=" * 80)
for i, ability in enumerate(below_70[:10], 1):
    print(f"\n{i}. Coverage: {ability['coverage']:.1%}")
    print(f"   Ability: {ability['jp']}")
    print(f"   Pattern matches:")
    for match in ability.get('pattern_matches', []):
        print(f"     - {match['pattern_name']}: {match['matched_text']}")
