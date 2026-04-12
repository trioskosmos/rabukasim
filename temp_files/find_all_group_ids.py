import json

with open('../data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

# Find abilities that have both group_enabled and group_id
for i, ability in enumerate(abilities):
    frames = ability.get('frames', [])
    for frame in frames:
        if frame.get('op') == 'LOOK_AND_CHOOSE' or frame.get('op') == 'ACTIVATE_MEMBER':
            attr = frame.get('attr', {})
            group_id = attr.get('group_id')
            group_enabled = attr.get('group_enabled')
            if group_id is not None:
                primary_text = ability.get('primary_text_jp', '')
                print(f"Index {i}: {primary_text[:80]}")
                print(f"  group_id: {group_id}, group_enabled: {group_enabled}")
                print(f"  Frame op: {frame.get('op')}")
                print()
