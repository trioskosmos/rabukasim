#!/usr/bin/env python3
"""Find specific extraction problems."""

import json
import re

with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("PROBLEMATIC EXTRACTIONS")
print("=" * 70)

problems = {
    'garbled_numbers': [],
    'duplicate_operations': [],
    'empty_after_trigger': [],
    'partial_branch_options': [],
    'weird_logic_flow': []
}

for ability in data['abilities']:
    source = ability['source_ability_texts'][0]
    logic = source['logic']
    jp = source['jp']
    cards = source['cards']
    card = cards[0] if cards else 'UNKNOWN'
    
    entry = {'card': card, 'jp': jp[:100], 'logic': logic}
    
    # Find garbled numbers like "cards1A1B"
    if re.search(r'[a-zA-Z]\d+[a-zA-Z]', logic):
        problems['garbled_numbers'].append(entry)
    
    # Find duplicate consecutive operations
    lines = logic.split('\n')
    for i in range(len(lines) - 1):
        if lines[i].strip() == lines[i+1].strip():
            problems['duplicate_operations'].append({**entry, 'dup_line': lines[i]})
            break
    
    # Find empty logic after trigger
    if logic.strip().startswith('{{') and len(lines) == 1:
        problems['empty_after_trigger'].append(entry)
    
    # Find partial branch options (has "choose one" but missing details)
    if 'choose one from:' in logic and ('option 1:' in logic and len(logic) < 50):
        problems['partial_branch_options'].append(entry)
    
    # Find weird flow (action before condition without "optional")
    for i, line in enumerate(lines):
        if i > 0 and line.strip().startswith('if ') and i < len(lines) - 1:
            prev_line = lines[i-1].strip()
            next_line = lines[i+1].strip()
            # If there's an action before the condition, and it's not optional
            if not prev_line.startswith('if ') and not prev_line.startswith('optional') and not next_line.startswith('if'):
                problems['weird_logic_flow'].append({**entry, 'issue': f'"{prev_line}" before "{line.strip()}"'})
                break
    
    # Limit
    for p in problems:
        if len(problems[p]) >= 5:
            break

import re

for prob_name, items in problems.items():
    if not items:
        continue
    
    print(f"\n{prob_name.upper().replace('_', ' ')} ({len(items)} shown)")
    print("-" * 70)
    
    for item in items[:3]:
        print(f"\nCard: {item['card']}")
        print(f"JP: {item['jp']}...")
        print(f"LOGIC: {item['logic'][:120]}...")
        if 'dup_line' in item:
            print(f"  ISSUE: Duplicate: '{item['dup_line']}'")
        if 'issue' in item:
            print(f"  ISSUE: {item['issue']}")

print("\n" + "=" * 70)
