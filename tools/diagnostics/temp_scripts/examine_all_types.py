#!/usr/bin/env python3
"""Examine multiple ability types and their extraction quality."""

import json

with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Sample by logic pattern
categories = {
    'draw_only': [],
    'discard_only': [],
    'draw_and_discard': [],
    'with_condition': [],
    'with_optional': [],
    'tap_or_target': [],
    'hearts_blades': [],
    'select_filters': [],
    'multi_step': [],
    'branch_choices': [],
    'complex_chains': []
}

for ability in data['abilities']:
    source = ability['source_ability_texts'][0]
    logic = source['logic']
    jp = source['jp']
    cards = source['cards']
    card = cards[0] if cards else 'UNKNOWN'
    
    entry = {'card': card, 'jp': jp[:120], 'logic': logic[:150], 'lines': len(logic.split('\n'))}
    
    lines = logic.split('\n')
    has_draw = 'draw' in logic
    has_discard = 'discard' in logic
    has_add = 'add' in logic
    has_if = 'if ' in logic
    has_optional = 'optional' in logic
    has_tap = 'tap' in logic
    has_heart = 'heart' in logic
    has_select = 'select' in logic
    has_choose = 'choose one' in logic
    
    # Categorize
    if has_draw and not has_discard and not has_if and not has_optional:
        categories['draw_only'].append(entry)
    elif has_discard and not has_draw and not has_if:
        categories['discard_only'].append(entry)
    elif has_draw and has_discard and not has_if:
        categories['draw_and_discard'].append(entry)
    elif has_if and not has_optional:
        categories['with_condition'].append(entry)
    elif has_optional:
        categories['with_optional'].append(entry)
    elif has_tap:
        categories['tap_or_target'].append(entry)
    elif has_heart:
        categories['hearts_blades'].append(entry)
    elif has_select:
        categories['select_filters'].append(entry)
    elif has_choose:
        categories['branch_choices'].append(entry)
    elif len(lines) >= 3:
        categories['multi_step'].append(entry)
    else:
        categories['complex_chains'].append(entry)
    
    # Limit each
    for cat in categories:
        if len(categories[cat]) > 3:
            break

print("ABILITY TYPE ANALYSIS")
print("=" * 70)

for cat_name, items in categories.items():
    if not items:
        continue
    
    print(f"\n{cat_name.upper().replace('_', ' ')} ({len(items)} shown)")
    print("-" * 70)
    
    for item in items[:2]:
        print(f"\nCard: {item['card']}")
        print(f"Lines: {item['lines']}")
        print(f"JP: {item['jp']}...")
        print(f"LOGIC: {item['logic']}...")

# Count totals
print("\n" + "=" * 70)
print("CATEGORY COUNTS")
print("=" * 70)

for cat_name, items in categories.items():
    total = sum(1 for a in data['abilities'] 
                if (cat_name == 'draw_only' and 'draw' in a['source_ability_texts'][0]['logic'] and 'discard' not in a['source_ability_texts'][0]['logic'])
                or (cat_name == 'with_condition' and 'if ' in a['source_ability_texts'][0]['logic'])
                or (cat_name == 'with_optional' and 'optional' in a['source_ability_texts'][0]['logic'])
                or (cat_name == 'branch_choices' and 'choose one' in a['source_ability_texts'][0]['logic']))
    print(f"{cat_name:20s}: {total:3d} abilities")
