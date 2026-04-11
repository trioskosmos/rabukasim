#!/usr/bin/env python3
"""Bulk fix ability frame mismatches"""
import json
import re

with open('ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

fixes_applied = []

for i, ab in enumerate(data['abilities']):
    text = ab.get('primary_text_jp', '')
    frames = ab.get('frames', [])
    card_refs = ab.get('card_refs', [])
    modified = False
    
    # Fix 1: LIVE_START text but ON_PLAY trigger -> change to LIVE_START (trigger_id 2)
    if 'ライブ開始時' in text and ab.get('trigger_id') == 1:
        old_trigger = ab['trigger']
        ab['trigger_id'] = 2
        ab['trigger'] = 'LIVE_START'
        for ref in card_refs:
            ref['trigger'] = 2
        fixes_applied.append(f'#{i}: Changed trigger ON_PLAY -> LIVE_START')
        modified = True
    
    # Fix 2: Mill from deck text but frames use HAND -> add source_zone: DECK
    if ('デッキの上から' in text or 'デッキを上から' in text):
        for frame in frames:
            if frame.get('op') == 'MOVE_TO_DISCARD':
                slot = frame.get('slot', {})
                if slot.get('target_slot') == 'HAND' and 'source_zone' not in slot:
                    slot['target_slot'] = 'DISCARD'
                    slot['source_zone'] = 'DECK'
                    attr = frame.get('attr', {})
                    if 'is_optional' in attr:
                        del attr['is_optional']
                    attr['target_player'] = 'SELF'
                    frame['attr'] = attr
                    fixes_applied.append(f'#{i}: Fixed mill source HAND -> DECK')
                    modified = True
                    break
    
    # Fix 3: ACTIVATED text but wrong trigger -> change to ACTIVATED (trigger_id 4)
    if '起動' in text and ab.get('trigger_id') != 4:
        old_trigger = ab['trigger']
        ab['trigger_id'] = 4
        ab['trigger'] = 'ACTIVATED'
        for ref in card_refs:
            ref['trigger'] = 4
        fixes_applied.append(f'#{i}: Changed trigger {old_trigger} -> ACTIVATED')
        modified = True
    
    # Fix 4: Check for missing PAY_ENERGY when E icons in activated abilities
    if ab.get('trigger_id') == 4 or '起動' in text:
        ee_count = text.count('{{icon_energy.png|E}}')
        has_pay = any(f.get('op') == 'PAY_ENERGY' for f in frames)
        if ee_count > 0 and not has_pay:
            fixes_applied.append(f'#{i}: WARNING - Missing PAY_ENERGY for {ee_count}E cost')
    
    # Fix 5: Check for missing DRAW frames
    draw_match = re.search(r'カードを(\d+)枚引', text)
    if draw_match:
        expected = int(draw_match.group(1))
        has_draw = any(f.get('op') == 'DRAW' for f in frames)
        if not has_draw:
            fixes_applied.append(f'#{i}: WARNING - Missing DRAW frame for draw {expected}')

# Save fixed file
with open('ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'Applied {len(fixes_applied)} fixes:')
for fix in fixes_applied[:50]:
    print(f'  {fix}')
if len(fixes_applied) > 50:
    print(f'  ... and {len(fixes_applied) - 50} more')
