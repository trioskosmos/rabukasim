import json
import re

with open('ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total abilities: {len(data["abilities"])}')
print(f'Version: {data.get("version", "unknown")}')
print()

issues = []
for i, ab in enumerate(data['abilities']):
    text = ab.get('primary_text_jp', '')
    trigger_id = ab.get('trigger_id')
    trigger = ab.get('trigger')
    frames = ab.get('frames', [])
    card_name = ab.get('card_refs', [{}])[0].get('name', 'unknown')
    
    # Check 1: LIVE_START text but ON_PLAY trigger
    if 'ライブ開始時' in text and trigger_id == 1:
        issues.append((i, 'TRIGGER_MISMATCH', f'LIVE_START text but ON_PLAY trigger', card_name))
    
    # Check 2: 起動 text but not ACTIVATED trigger
    if '起動' in text and trigger_id != 4:
        issues.append((i, 'TRIGGER_MISMATCH', f'ACTIVATED text but trigger={trigger}', card_name))
    
    # Check 3: Mill from deck but frames use HAND
    if ('デッキの上から' in text or 'デッキを上から' in text):
        for frame in frames:
            if frame.get('op') == 'MOVE_TO_DISCARD':
                slot = frame.get('slot', {})
                if slot.get('target_slot') == 'HAND' and 'source_zone' not in slot:
                    issues.append((i, 'SOURCE_MISMATCH', f'Mill deck text but HAND source', card_name))
                    break
    
    # Check 4: Draw text but no DRAW frame or wrong value
    draw_match = re.search(r'カードを(\d+)枚引', text)
    if draw_match:
        expected_draw = int(draw_match.group(1))
        draw_frames = [f for f in frames if f.get('op') == 'DRAW']
        if not draw_frames:
            issues.append((i, 'MISSING_DRAW', f'Draw {expected_draw} text but no DRAW frame', card_name))
        else:
            for df in draw_frames:
                if df.get('value') != expected_draw and df.get('attr', {}).get('compare_accumulated') != 1:
                    issues.append((i, 'DRAW_MISMATCH', f'Draw {expected_draw} text but frame value={df.get("value")}', card_name))
    
    # Check 5: EE cost in text but no PAY_ENERGY
    ee_count = text.count('{{icon_energy.png|E}}')
    if ee_count > 0 and '起動' in text:
        pay_frames = [f for f in frames if f.get('op') == 'PAY_ENERGY']
        if not pay_frames:
            issues.append((i, 'MISSING_PAY', f'{ee_count}E cost but no PAY_ENERGY', card_name))
        else:
            for pf in pay_frames:
                if pf.get('value') != ee_count and pf.get('attr', {}).get('is_optional') != 1:
                    issues.append((i, 'PAY_MISMATCH', f'{ee_count}E cost but PAY_ENERGY value={pf.get("value")}', card_name))

print(f'Found {len(issues)} potential issues:')
for idx, issue_type, desc, name in issues[:50]:
    print(f'  Ability #{idx} ({name}): [{issue_type}] {desc}')

# Save detailed report
with open('ability_issues_report.txt', 'w', encoding='utf-8') as out:
    out.write(f'Ability Analysis Report\n')
    out.write(f'Total abilities: {len(data["abilities"])}\n')
    out.write(f'Issues found: {len(issues)}\n\n')
    for idx, issue_type, desc, name in issues:
        out.write(f'Ability #{idx} ({name}): [{issue_type}] {desc}\n')
        
print(f'\nDetailed report saved to ability_issues_report.txt')
