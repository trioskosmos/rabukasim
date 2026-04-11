#!/usr/bin/env python3
"""Manual validation of ability frames against text descriptions"""
import json
import re

with open('ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

issues = []

for i, ab in enumerate(data['abilities']):
    text = ab.get('primary_text_jp', '')
    trigger_id = ab.get('trigger_id')
    trigger = ab.get('trigger', '')
    frames = ab.get('frames', [])
    
    # Skip abilities with empty text
    if not text:
        continue
    
    # Check 1: Trigger consistency
    if 'ライブ開始時' in text and '登場' not in text and trigger_id != 2:
        # Pure LIVE_START ability
        issues.append((i, 'TRIGGER', f'LIVE_START text but trigger={trigger}', ab.get('card_refs', [{}])[0].get('name', 'unknown')))
    
    if '起動' in text and trigger_id != 4:
        # Should be ACTIVATED
        issues.append((i, 'TRIGGER', f'ACTIVATED text but trigger={trigger}', ab.get('card_refs', [{}])[0].get('name', 'unknown')))
    
    # Check 2: Mill from deck
    if 'デッキの上からカードを' in text or 'デッキを上から' in text:
        # Check if any MOVE_TO_DISCARD has wrong source
        for frame in frames:
            if frame.get('op') == 'MOVE_TO_DISCARD':
                slot = frame.get('slot', {})
                if slot.get('target_slot') == 'HAND' and 'source_zone' not in slot:
                    issues.append((i, 'SOURCE', 'Mill text but no DECK source', ab.get('card_refs', [{}])[0].get('name', 'unknown')))
                    break
    
    # Check 3: Energy cost in ACTIVATED abilities
    if trigger_id == 4 or '起動' in text:
        ee_count = text.count('{{icon_energy.png|E}}')
        has_pay = any(f.get('op') == 'PAY_ENERGY' for f in frames)
        if ee_count > 0 and not has_pay:
            issues.append((i, 'PAY', f'Missing PAY_ENERGY for {ee_count}E cost', ab.get('card_refs', [{}])[0].get('name', 'unknown')))
    
    # Check 4: Draw cards
    draw_match = re.search(r'カードを(\d+)枚引', text)
    if draw_match:
        expected = int(draw_match.group(1))
        has_draw = any(f.get('op') == 'DRAW' and f.get('value') == expected for f in frames)
        if not has_draw:
            # Check if it uses compare_accumulated pattern
            has_conditional = any(f.get('op') == 'DRAW' and f.get('attr', {}).get('compare_accumulated') for f in frames)
            if not has_conditional:
                issues.append((i, 'DRAW', f'Missing DRAW {expected}', ab.get('card_refs', [{}])[0].get('name', 'unknown')))

# Print results
print(f'Validated {len(data["abilities"])} abilities')
print(f'Found {len(issues)} real issues:')
print()

for idx, issue_type, desc, name in sorted(issues, key=lambda x: x[0]):
    print(f'Ability #{idx} ({name}): [{issue_type}] {desc}')

# Save to file
with open('validated_issues.txt', 'w', encoding='utf-8') as f:
    f.write(f'Validated Ability Issues\n')
    f.write(f'Total abilities: {len(data["abilities"])}\n')
    f.write(f'Real issues found: {len(issues)}\n\n')
    for idx, issue_type, desc, name in sorted(issues, key=lambda x: x[0]):
        f.write(f'Ability #{idx} ({name}): [{issue_type}] {desc}\n')

print(f'\nSaved to validated_issues.txt')
