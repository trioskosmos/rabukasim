import json

# Load authored frames
with open('data/ability_frame_source_authored.json', 'r', encoding='utf-8') as f:
    authored = json.load(f)

# Find PL!N-bp1-003-R+ frames
for ability in authored['abilities']:
    for ref in ability.get('card_refs', []):
        if ref.get('card_no') == 'PL!N-bp1-003-R+':
            print(f"Card: {ref.get('card_no')}, Ability Index: {ref.get('ability_index')}")
            print(f"Trigger: {ref.get('trigger')}")
            print(f"Frames:")
            for i, frame in enumerate(ability.get('frames', [])):
                print(f"  {i}: {frame.get('op')} | value={frame.get('value')} | attr={frame.get('attr')} | slot={frame.get('slot')}")
            print()
