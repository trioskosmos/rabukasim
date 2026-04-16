#!/usr/bin/env python3
"""
Extract all costs from abilities_extracted_from_cards.json to JSON format.
This script reads: ../data/abilities_extracted_from_cards.json
This script writes: ../data/all_costs.json
"""

import json

with open('../data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Group by cost type
cost_types = {}
null_costs = []

for i, ab in enumerate(data['unique_abilities'], 1):
    cost = ab.get('cost')
    triggerless = ab['triggerless_text']
    
    # Extract raw cost text before colon
    raw_cost = triggerless.split('：')[0] if '：' in triggerless else triggerless.split(':')[0]
    raw_cost = raw_cost.strip() if '：' in triggerless or ':' in triggerless else None
    
    if cost is None:
        null_costs.append({
            'index': i,
            'raw_cost': raw_cost,
            'triggerless': triggerless,
            'card_count': ab['card_count'],
            'cards': ab['cards']
        })
    elif isinstance(cost, dict):
        for cost_type in cost.keys():
            if cost_type not in cost_types:
                cost_types[cost_type] = []
            cost_types[cost_type].append({
                'index': i,
                'raw_cost': raw_cost,
                'cost': cost,
                'triggerless': triggerless,
                'card_count': ab['card_count'],
                'cards': ab['cards']
            })
    elif isinstance(cost, str):
        if 'raw_fallback' not in cost_types:
            cost_types['raw_fallback'] = []
        cost_types['raw_fallback'].append({
            'index': i,
            'raw_cost': raw_cost,
            'fallback': cost,
            'triggerless': triggerless,
            'card_count': ab['card_count'],
            'cards': ab['cards']
        })

# Build output structure
output = {
    "generated_by": "tools/extract_all_costs.py",
    "source_file": "../data/abilities_extracted_from_cards.json",
    "total_abilities": len(data['unique_abilities']),
    "total_cost_types": len(cost_types),
    "null_costs_count": len(null_costs),
    "cost_types": {}
}

for cost_type, items in sorted(cost_types.items()):
    output["cost_types"][cost_type] = {
        "count": len(items),
        "items": items
    }

if null_costs:
    output["null_costs"] = {
        "count": len(null_costs),
        "items": null_costs
    }

# Write to JSON file
with open('../data/all_costs.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# Write to TXT file
txt_output = []
txt_output.append("=" * 80)
txt_output.append("ALL COSTS FROM ABILITIES_EXTRACTED_FROM_CARDS.JSON")
txt_output.append("=" * 80)
txt_output.append(f"Total abilities: {len(data['unique_abilities'])}")
txt_output.append("")

# Output by cost type
for cost_type, items in sorted(cost_types.items()):
    txt_output.append(f"\n{'=' * 80}")
    txt_output.append(f"COST TYPE: {cost_type}")
    txt_output.append(f"Count: {len(items)}")
    txt_output.append("=" * 80)
    
    for item in items:
        txt_output.append(f"\n[{item['index']}] Raw: {item['raw_cost']}")
        txt_output.append(f"    Structured: {item.get('cost', 'NO COST KEY')}")
        txt_output.append(f"    Cards: {item['card_count']}")

# Output null costs
if null_costs:
    txt_output.append(f"\n{'=' * 80}")
    txt_output.append(f"COST TYPE: null (no cost)")
    txt_output.append(f"Count: {len(null_costs)}")
    txt_output.append("=" * 80)
    
    for item in null_costs[:20]:  # Show first 20
        txt_output.append(f"\n[{item['index']}] Raw: {item['raw_cost']}")
        txt_output.append(f"    Cards: {item['card_count']}")
    
    if len(null_costs) > 20:
        txt_output.append(f"\n... and {len(null_costs) - 20} more null costs")

with open('../data/all_costs.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(txt_output))

print(f"Extracted all costs to ../data/all_costs.json")
print(f"Extracted all costs to ../data/all_costs.txt")
print(f"Total cost types: {len(cost_types)}")
print(f"Null costs: {len(null_costs)}")
