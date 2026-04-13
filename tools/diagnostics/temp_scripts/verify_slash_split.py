#!/usr/bin/env python3
import json

# Check if slash-separated triggers are correctly split
with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Checking for split slash-separated triggers in output...")

# Look for abilities that might have been split from slash format
found = []
for ability in data['abilities']:
    jp = ability['source_ability_texts'][0]['jp']
    trigger = ability['trigger']
    # Check for part 1 of slash-separated (just toujyou without slash)
    if '{{toujyou.png' in jp and '/{{' not in jp:
        found.append((trigger, jp[:100]))

print(f"\nFound {len(found)} abilities with toujyou icon (potentially split)")
for trigger, jp in found[:5]:
    print(f"  [{trigger}] {jp}...")

# Check for live_start that was split
live_start_count = 0
for ability in data['abilities']:
    jp = ability['source_ability_texts'][0]['jp']
    if jp.strip().startswith('{{live_start.png'):
        live_start_count += 1

print(f"\nAbilities starting with live_start: {live_start_count}")

# Check for toujyou that was split
on_play_count = 0
for ability in data['abilities']:
    jp = ability['source_ability_texts'][0]['jp']
    if jp.strip().startswith('{{toujyou.png'):
        on_play_count += 1

print(f"Abilities starting with toujyou (ON_PLAY): {on_play_count}")
