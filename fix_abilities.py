#!/usr/bin/env python3
"""Script to find and fix ability frames"""
import json

with open(r'C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

# Find ability #6 (Ozawa Rurino)
for i, ab in enumerate(abilities):
    card_refs = ab.get('card_refs', [])
    for ref in card_refs:
        if 'bp5-011' in ref.get('card_no', ''):
            print(f"Ability #{i}: {ref.get('name', 'Unknown')}")
            print(f"  Card No: {ref.get('card_no', 'Unknown')}")
            print(f"  Primary Text: {ab.get('primary_text_jp', 'N/A')[:60]}...")
            frames = ab.get('frames', [])
            print(f"  Frames ({len(frames)}):")
            for j, frame in enumerate(frames):
                print(f"    [{j}] {frame.get('op', 'N/A')}")
            print()
            break

# Find all abilities with SELECT_MODE but no option_names
print("\n=== Abilities with SELECT_MODE but missing option_names ===")
for i, ab in enumerate(abilities):
    frames = ab.get('frames', [])
    has_select_mode = any(f.get('op') == 'SELECT_MODE' for f in frames)
    has_option_names = 'option_names' in ab

    if has_select_mode and not has_option_names:
        card_refs = ab.get('card_refs', [])
        card_no = card_refs[0].get('card_no', 'Unknown') if card_refs else 'Unknown'
        name = card_refs[0].get('name', 'Unknown') if card_refs else 'Unknown'
        select_count = [f for f in frames if f.get('op') == 'SELECT_MODE'][0].get('value', 0)
        print(f"#{i}: {name} ({card_no}) - {select_count} options")
        print(f"   Text: {ab.get('primary_text_jp', 'N/A')[:50]}...")

print("\n=== Done ===")
