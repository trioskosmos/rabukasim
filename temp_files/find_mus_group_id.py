import json

with open('../data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

# Find abilities that reference μ's to see what group_id they use
for i, ability in enumerate(abilities):
    primary_text = ability.get('primary_text_jp', '')
    if "μ's" in primary_text or "μ" in primary_text:
        frames = ability.get('frames', [])
        for frame in frames:
            if frame.get('op') == 'LOOK_AND_CHOOSE':
                attr = frame.get('attr', {})
                group_id = attr.get('group_id')
                group_enabled = attr.get('group_enabled')
                if group_id is not None or group_enabled:
                    print(f"Index {i}: {primary_text[:80]}")
                    print(f"  group_id: {group_id}, group_enabled: {group_enabled}")
                    print(f"  Frame: {frame}")
                    print()
