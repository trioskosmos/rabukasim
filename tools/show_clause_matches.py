import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

if len(sys.argv) < 2:
    print("Usage: python show_clause_matches.py <pattern_name>")
    sys.exit(1)

pattern_name = sys.argv[1]

with open('data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get clause matches for the pattern
clause_matches = data['analysis']['dsl_pattern_analysis'].get('clause_matches', {})

if pattern_name in clause_matches:
    matches = clause_matches[pattern_name]
    print(f"Pattern: {pattern_name}")
    print(f"Total matches: {len(matches)}")
    print()
    print("First 20 matches:")
    for i, match in enumerate(matches[:20], 1):
        print(f"  {i}. {match}")
    
    if len(matches) > 20:
        print(f"  ... and {len(matches) - 20} more")
else:
    print(f"Pattern '{pattern_name}' not found in clause_matches")
