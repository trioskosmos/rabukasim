import json

with open('../data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']

# Search for any frame that might have MUSE or similar group_id
for i, ability in enumerate(abilities):
    frames = ability.get('frames', [])
    for frame in frames:
        attr = frame.get('attr', {})
        group_id = attr.get('group_id')
        if group_id and ('MUSE' in str(group_id).upper() or 'MU' in str(group_id).upper()):
            primary_text = ability.get('primary_text_jp', '')
            print(f"Index {i}: {primary_text[:80]}")
            print(f"  group_id: {group_id}")
            print()

# Also check all unique group_id values
group_ids = set()
for ability in abilities:
    for frame in ability.get('frames', []):
        attr = frame.get('attr', {})
        group_id = attr.get('group_id')
        if group_id:
            group_ids.add(group_id)

print("All unique group_id values:")
for gid in sorted(group_ids):
    print(f"  {gid}")
