import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

if len(sys.argv) < 2:
    print("Usage: python show_unique_matches.py <pattern_name>")
    sys.exit(1)

pattern_name = sys.argv[1]

with open('data/dsl_analysis_structured.json', 'r', encoding='utf-8') as f:
    dsl_data = json.load(f)

# Find the pattern
for pattern in dsl_data['patterns']:
    if pattern['pattern_name'] == pattern_name:
        print(f"Pattern: {pattern_name}")
        print(f"Match count: {pattern['match_count']}")
        print()
        print("Unique ability texts:")
        unique_texts = set()
        for ability in pattern['matched_abilities']:
            unique_texts.add(ability['ability_text'])
        
        for i, text in enumerate(list(unique_texts)[:20], 1):
            print(f"  {i}. {text}")
        
        if len(unique_texts) > 20:
            print(f"  ... and {len(unique_texts) - 20} more")
        sys.exit(0)

print(f"Pattern '{pattern_name}' not found")
