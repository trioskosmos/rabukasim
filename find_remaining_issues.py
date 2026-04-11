#!/usr/bin/env python3
import json

with open('data/ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']
issues = []

for i, a in enumerate(abilities):
    text = a.get('primary_text_jp', '')
    frames = a.get('frames', [])
    card = a.get('card_refs', [{}])[0].get('card_no', f'idx{i}')
    
    # Check for group filters needed
    groups = ["μ's", 'Aqours', '虹ヶ咲', 'Liella!', '蓮ノ空']
    group_ids = ['MUSE', 'AQOURS', 'NIJIGASAKI', 'LIELLA', 'HASUNOSORA']
    for g, gid in zip(groups, group_ids):
        if g in text and 'メンバー' in text:
            has_group = any(f.get('attr',{}).get('group_id')==gid for f in frames)
            if not has_group:
                issues.append((i, card, 'MISSING_GROUP_FILTER', gid, text[:60]))
                break

print(f'Found {len(issues)} issues:')
for idx, card, issue_type, detail, text in issues[:10]:
    print(f'  [{idx}] {card}: {issue_type} ({detail})')
    print(f'      Text: {text}...')
