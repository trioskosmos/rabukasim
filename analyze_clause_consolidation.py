import json
import sys
from difflib import SequenceMatcher
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

# Function to calculate similarity
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Group similar clauses (>= 80% similarity)
clause_groups = []
processed = set()

for clause1, count1 in sorted(all_clauses.items(), key=lambda x: -x[1]):
    if clause1 in processed:
        continue
    
    group = [clause1]
    processed.add(clause1)
    
    for clause2, count2 in all_clauses.items():
        if clause2 in processed:
            continue
        
        if similarity(clause1, clause2) >= 0.8:
            group.append(clause2)
            processed.add(clause2)
    
    if len(group) > 1:
        group_count = sum(all_clauses[c] for c in group)
        clause_groups.append((group, group_count))

# Sort by total count
clause_groups.sort(key=lambda x: -x[1])

print(f"Total unique clause patterns: {len(all_clauses)}")
print(f"Number of similar clause groups (>=80% similarity): {len(clause_groups)}")
print(f"\nTop 20 similar clause groups:")
for i, (group, count) in enumerate(clause_groups[:20], 1):
    print(f"\nGroup {i} (total {count} occurrences):")
    for clause in group:
        print(f"  - '{clause}' ({all_clauses[clause]})")
