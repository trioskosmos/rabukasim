#!/usr/bin/env python3
"""Scan all abilities and identify those needing fixes"""
import json

with open(r'C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

# Find abilities with SELECT_MODE but missing option_names
missing_option_names = []
for i, ab in enumerate(abilities):
    frames = ab.get('frames', [])
    has_select_mode = any(f.get('op') == 'SELECT_MODE' for f in frames)
    has_option_names = 'option_names' in ab

    if has_select_mode and not has_option_names:
        card_refs = ab.get('card_refs', [])
        if card_refs:
            card_no = card_refs[0].get('card_no', 'Unknown')
            name = card_refs[0].get('name', 'Unknown')
            select_frame = [f for f in frames if f.get('op') == 'SELECT_MODE'][0]
            select_count = select_frame.get('value', 0)
            missing_option_names.append({
                'index': i,
                'card_no': card_no,
                'name': name,
                'options': select_count,
                'text': ab.get('primary_text_jp', '')[:80]
            })

print(f"=== Abilities with SELECT_MODE but missing option_names: {len(missing_option_names)} ===")
for item in missing_option_names[:30]:  # Show first 30
    print(f"#{item['index']}: {item['name']} ({item['card_no']}) - {item['options']} options")
    print(f"   Text: {item['text']}...")

print(f"\nTotal remaining: {len(missing_option_names)}")
