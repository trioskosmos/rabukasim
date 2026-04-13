#!/usr/bin/env python3
import json

# Check ability_frame_source.json for slash-separated triggers
with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Searching ability_frame_source.json for slash-separated triggers...")
count = 0
for ability in data.get('abilities', []):
    jp = ability.get('primary_text_jp', '')
    if '/' in jp:
        # Check if it looks like multiple triggers
        parts = jp.split('/')
        if len(parts) >= 2:
            count += 1
            if count <= 5:
                print(f"\n--- Ability {count} ---")
                print(f"Trigger: {ability.get('trigger', 'N/A')}")
                print(f"Full text: {jp[:200]}...")
                for i, part in enumerate(parts):
                    print(f"  Part {i+1}: {part[:80]}...")

print(f"\nTotal slash-separated in source: {count}")
