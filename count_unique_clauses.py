import json
import sys
sys.path.append('tools/ability_extraction')
from extract_card_abilities import parse_grammar_clauses

# Load the coverage log which has template data
with open('data/ability_coverage_log.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract all unique clauses from all templates
all_clauses = {}

for template_data in data.get('templates', []):
    template = template_data.get('template', '')
    clauses = parse_grammar_clauses(template)
    
    for clause in clauses:
        if clause.strip() and clause != '。':
            all_clauses[clause] = all_clauses.get(clause, 0) + template_data.get('usage_count', 1)

# Sort by frequency
sorted_clauses = sorted(all_clauses.items(), key=lambda x: -x[1])

print(f"Total unique clause patterns: {len(all_clauses)}")
print(f"\nTop 30 most common clause patterns:")
for i, (clause, count) in enumerate(sorted_clauses[:30], 1):
    print(f"{i}. '{clause}' (appears in {count} templates)")
