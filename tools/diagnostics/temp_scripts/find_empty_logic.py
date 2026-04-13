#!/usr/bin/env python3
"""Find and analyze empty logic fields in abilities_extracted.json"""

import json

with open('data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

empty_abilities = []
incomplete_abilities = []
japanese_text_abilities = []

for i, ability in enumerate(data.get('abilities', [])):
    for j, source_text in enumerate(ability.get('source_ability_texts', [])):
        jp = source_text.get('jp', '')
        logic = source_text.get('logic', '')
        
        # Truly empty logic
        if not logic or logic.strip() == '':
            empty_abilities.append({
                'index': i,
                'sub_index': j,
                'jp': jp,
                'logic': logic,
                'cards': source_text.get('cards', [])
            })
        # Logic with Japanese text
        elif any(ord(c) > 127 for c in logic):
            japanese_text_abilities.append({
                'index': i,
                'sub_index': j,
                'jp': jp,
                'logic': logic,
                'cards': source_text.get('cards', [])
            })
        # Incomplete logic (very short compared to jp)
        elif len(logic) < 20 and len(jp) > 50:
            incomplete_abilities.append({
                'index': i,
                'sub_index': j,
                'jp': jp,
                'logic': logic,
                'cards': source_text.get('cards', [])
            })

print(f"=== Empty Logic Fields ({len(empty_abilities)}) ===")
for item in empty_abilities[:10]:  # Show first 10
    print(f"\nIndex {item['index']}.{item['sub_index']}:")
    print(f"  JP: {item['jp']}")
    print(f"  Logic: '{item['logic']}'")
    print(f"  Cards: {len(item['cards'])}")

print(f"\n=== Logic with Japanese Text ({len(japanese_text_abilities)}) ===")
for item in japanese_text_abilities[:10]:  # Show first 10
    print(f"\nIndex {item['index']}.{item['sub_index']}:")
    print(f"  JP: {item['jp']}")
    print(f"  Logic: {item['logic']}")
    print(f"  Cards: {len(item['cards'])}")

print(f"\n=== Incomplete Logic ({len(incomplete_abilities)}) ===")
for item in incomplete_abilities[:10]:  # Show first 10
    print(f"\nIndex {item['index']}.{item['sub_index']}:")
    print(f"  JP: {item['jp']}")
    print(f"  Logic: {item['logic']}")
    print(f"  Cards: {len(item['cards'])}")

print(f"\nTotal empty: {len(empty_abilities)}")
print(f"Total with Japanese text: {len(japanese_text_abilities)}")
print(f"Total incomplete: {len(incomplete_abilities)}")
