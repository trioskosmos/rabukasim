#!/usr/bin/env python3
"""
Analyze clause positions to find which abilities have the most clauses.
"""

import json
import sys
sys.path.insert(0, 'tools/ability_extraction')

from extract_card_abilities import parse_grammar_clauses

# Load the extracted abilities
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['unique_abilities']

# Analyze clause counts for each ability
clause_counts = []
for ability in abilities:
    template = ability['combined_template']
    clauses = parse_grammar_clauses(template)
    clause_count = len(clauses)
    
    if clause_count > 0:
        clause_counts.append({
            'template': template,
            'clauses': clauses,
            'count': clause_count,
            'full_text': ability['full_text'],
            'card_count': ability['card_count']
        })

# Sort by clause count descending
clause_counts.sort(key=lambda x: x['count'], reverse=True)

# Find the maximum clause count
max_count = max(item['count'] for item in clause_counts) if clause_counts else 0

print(f"Total abilities analyzed: {len(abilities)}")
print(f"Maximum clause count: {max_count}")
print(f"Number of abilities with {max_count} clauses: {sum(1 for item in clause_counts if item['count'] == max_count)}")

# Show the ability with maximum clause count
print(f"\n=== ABILITY WITH {max_count} CLAUSES ===\n")
for item in clause_counts:
    if item['count'] == max_count:
        print(f"Template: {item['template']}")
        print(f"Full text: {item['full_text']}")
        print(f"Card count: {item['card_count']}")
        print(f"\nClauses ({item['count']} total):")
        for j, clause in enumerate(item['clauses'], 1):
            print(f"  {j}. '{clause}'")
        print()
        break

# Show the ability with 30 clauses
if max_count == 30:
    print(f"\n=== ABILITY WITH 30 CLAUSES ===\n")
    for item in clause_counts:
        if item['count'] == 30:
            print(f"Template: {item['template']}")
            print(f"Full text: {item['full_text']}")
            print(f"Card count: {item['card_count']}")
            print(f"\nClauses ({item['count']} total):")
            for j, clause in enumerate(item['clauses'], 1):
                print(f"  {j}. '{clause}'")
            print()
            break
