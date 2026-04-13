import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Search for pattern variables in abilities_extracted.json
if len(sys.argv) < 2:
    print("Usage: python search_pattern_variables.py <pattern_name>")
    sys.exit(1)

pattern_name = sys.argv[1]

with open('data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

pattern_variables = data['analysis']['dsl_pattern_analysis']['pattern_variables']

if pattern_name in pattern_variables:
    variables_list = pattern_variables[pattern_name]
    print(f"Pattern: {pattern_name}")
    print(f"Total matches: {len(variables_list)}")
    print()
    print("First 10 variable sets:")
    for i, vars in enumerate(variables_list[:10], 1):
        print(f"  {i}. {vars}")
else:
    print(f"Pattern '{pattern_name}' not found")
