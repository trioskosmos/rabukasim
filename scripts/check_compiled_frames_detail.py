import json

with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    compiled = json.load(f)

card_47 = compiled['live_db']['47']
abilities = card_47.get('abilities', [])

print(f"Card 47: {card_47.get('name', 'Unknown')}")

for idx, ability in enumerate(abilities):
    print(f"\nAbility {idx}:")
    print(f"  Trigger: {ability.get('trigger', 'Unknown')}")
    frame_program = ability.get('frame_program', {})
    frames = frame_program.get('frames', [])
    print(f"  Frames count: {len(frames)}")
    
    for f_idx, frame in enumerate(frames):
        print(f"\n  Frame {f_idx}:")
        for key in sorted(frame.keys()):
            value = frame[key]
            if key == 'attr' and isinstance(value, dict):
                print(f"    {key}:")
                for attr_key in sorted(value.keys()):
                    print(f"      {attr_key}: {value[attr_key]}")
            else:
                print(f"    {key}: {value}")
